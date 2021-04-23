from tkinter import *
from tkinter import colorchooser, filedialog, ttk
from functools import partial
import pyautogui as pg
from PIL import Image, ImageTk
import datetime, os, cv2, threading


#-------===Program Overview===-------#
# The following code is for a python animator,
# this is basically paint, but you can animate all the images you saved.
# Basically, you paint and save your frames, they show up on the picture 
# bar below, and then you can compile all the frames together to make an animation!


#The main--and only--class for the whole program F
class PaintApp():
    def __init__(self):
        #initlaize the main variables for the project, put them all in one line, because yes
        self.currentX, self.currentY, self.currentWidth, self.colorIndex, self.videoFrameRate, self.currentColor, self.colorHistory = 0, 0, 1, -1, 10, "black", []
        self.parentDir = os.path.dirname(os.path.realpath(__file__)) #get the path where the script is currently located
        self.imageDir = os.path.join(self.parentDir, "savedImages") #image dir where the images will be stored
        self.completedDir = os.path.join(self.parentDir, "Completed Animations") #where the completed animations will be stored

        #initialize the basic root, etc
        self.main = Tk()
        self.main.title("Animator Pog")
        self.main.state("zoomed")
        self.main.rowconfigure(1, weight=1)
        self.main.columnconfigure(1, weight=1)

        self.sideBar = Frame(self.main, height=830) #The side bar containing everything like save, pick color, etc
        self.sideBar.place(x=7, y=7)

        #Run all the main functions
        self.initFolders()
        self.initMenu()
        self.initCanvas()
        self.initSideBar()  
        self.initPicturesBar(False)    
        self.initKeyBinds()

        self.main.mainloop()

    #makes the painting areas
    def initCanvas(self):
        self.canvas = Canvas(self.main, bg="#e8e9ed", width=1750, height=830, highlightthickness=2, highlightbackground="blue")
        self.canvas.grid(row=0, column=2)

        self.canvasFunctions() #make the canvas actually do stuff, like draw 

    #adds all the buttons to the side bar, with their own properties 
    def initSideBar(self):
        self.colorButton = Button(self.sideBar, text="Pick Color", width=20, height=2, bg="#ffffff", command=self.colorFunc)
        self.colorButton.pack(pady=(0,3))
        self.eraserButton = Button(self.sideBar, text="Eraser", width=20, height=2, bg="#e2aeb4", state=ACTIVE, command=self.eraserFunc)
        self.eraserButton.pack(pady=(0,3))
        clearButton = Button(self.sideBar, text="Clear", width=20, height=2, bg="#00ffd5", command=self.clearFunc).pack(pady=(0,3))
        saveButton = Button(self.sideBar, text="Save Image", width=20, height=2, bg="#26D701", command=self.saveFile).pack(pady=(0,3))
        animateButton = Button(self.sideBar, text="Animate", width=20, height=2, bg="#45B6FE", command=self.animate).pack(pady=(0,3))
        widthScale = Scale(self.sideBar, label="Brush Size", orient=HORIZONTAL, from_=1, to=100, command=self.widthFunc).pack(pady=(0,3))
        frameScale = Scale(self.sideBar, label="Frame Rate", orient=HORIZONTAL, from_=1, to=60, command=self.frameFunc)
        frameScale.pack(pady=(0,3))
        frameScale.set(10) #setting the initial value of the scale to be 10
        
        historyLabel = Label(self.sideBar, text="-Recent Swatches-", font=("Arial", 13), fg="blue").pack()

        self.swatchFrame = Frame(self.sideBar) #makes the frame to store recent swtaches
        self.swatchFrame.pack() 

        # refreshButton = Button(self.sideBar, text="Refresh Frames Bar", width=20, height=2, bg="#db2c2c", command= lambda: self.initPicturesBar(True)).pack(pady=(309,0)) #bad sadge
        deleteButton = Button(self.sideBar, text="Delete All Frames", width=20, height=2, bg="#db2c2c", command=self.deleteAll).pack(pady=(309,3))
        exitButton = Button(self.sideBar, text="Exit", width=20, height=2, bg="#ff0000", command=self.main.quit).pack(pady=5)

    #initialize the menu up at the top where it says, "File" with it's components
    def initMenu(self):
        self.mainBar = Menu(self.main)
        self.main.config(menu=self.mainBar)

        fileMenu = Menu(self.mainBar, tearoff=0)
        self.mainBar.add_cascade(label="File", menu=fileMenu) 
        self.fileMenuCommands(fileMenu) #adding the commands

    #make the folders if they dont already exist
    def initFolders(self):
        subDir = [sub for sub in os.listdir(self.parentDir) if os.path.isdir(sub)] #checking every sub directory of the currect dir
        
        if "savedImages" not in subDir:
            os.mkdir(self.imageDir)
        if "Completed Animations" not in subDir:
            os.mkdir(self.parentDir+r"\Completed Animations")

    #make the "pictures bar" where all the frames are stored for the user to see
    def initPicturesBar(self, needToUpdate=False):
        scrollFrame = Frame(self.main, width=1080) #the main frame
        scrollFrame.place(x=0, y=850, anchor="nw", relwidth=1)

        scrollCanvas = Canvas(scrollFrame, height=119) #the canvas inside the frame, because canvas = scrollable
        scrollCanvas.pack(side=TOP, fill=X, expand=True)

        scrollBar = ttk.Scrollbar(scrollFrame, orient=HORIZONTAL, command=scrollCanvas.xview) #init the scrollbar into the main frame
        scrollBar.pack(side=TOP, fill=X)

        scrollCanvas.configure(xscrollcommand=scrollBar.set) #configure it for xscroll
        scrollCanvas.bind("<Configure>", lambda e: scrollCanvas.configure(scrollregion=scrollCanvas.bbox("all"))) # configure bounding box, for the canvas 

        #executes when you scroll in the canvas area
        def mouseWheelEvent(event):
            scrollCanvas.xview_scroll(-1 * int((event.delta / 120)), "units")

        scrollCanvas.bind_all("<MouseWheel>", mouseWheelEvent) #binding the scroll to the func

        self.innerFrame = Frame(scrollCanvas) #the "second" but VERY import frame to the canvas (NOTE: add all your items here)
        scrollCanvas.create_window((0, 0), window=self.innerFrame, anchor="nw") #creating a window with the windo being the inner frame

        
        for widget in self.innerFrame.winfo_children():  #destroy all the objects in the frame
            widget.destroy()

        for im in os.listdir(self.imageDir): #add all the pictures in the directory to the frame
            path = os.path.join(self.imageDir, im)
            imageOpen = Image.open(path)
            tempImage = imageOpen.resize((245, 116)) #resizing the image to make it fit, but maintain aspect ratio

            photo=ImageTk.PhotoImage(tempImage)
            picLabel = Button(self.innerFrame, text=photo, borderwidth=0, command= lambda path=path: self.showPic(path)) #make a button with the image, but remove border
            picLabel.image= photo #NOTE: if you dont have this IT WONT WORK (I learned the hard way)
            picLabel.configure(image=photo) #configure it with the photo
            picLabel.pack(side=LEFT, padx=10) #make the padx to 10, to it leaves a gap

            if needToUpdate: #if need to we have to update the the canvas 
                scrollCanvas.config(scrollregion=scrollCanvas.bbox("all")) #as well ad redefine it's scroll region
                scrollCanvas.update_idletasks()

    #make the keybinds, (not global) so wont work outside the root window
    def initKeyBinds(self):
        self.main.bind("<Control-s>", self.saveFile)
        self.main.bind("<space>", self.saveFile)

    #when the image is clicked on, this is callback func to show it
    def showPic(self, path):
        img = Image.open(path)
        img.show()

    #binding the button to actually draw
    def canvasFunctions(self):
        self.canvas.bind("<Button-1>", self.locateXY)
        self.canvas.bind("<B1-Motion>", self.drawLine)

    #gets the XY
    def locateXY(self, event):
        self.currentX, self.currentY = event.x, event.y

    #Actually draws the line
    def drawLine(self, event):
        self.canvas.create_line((self.currentX, self.currentY, event.x, event.y), fill=self.currentColor, width=self.currentWidth, capstyle=ROUND, joinstyle=ROUND , smooth=True, splinesteps=64)
        self.currentX, self.currentY = event.x, event.y

    #changes the color, and adds it to color history
    def colorFunc(self):
        self.color = colorchooser.askcolor(title ="Pick Color...")
        self.currentColor = self.color[1]

        self.colorHistory.append(self.color[1])
        self.updateColorHistory(self.colorHistory) #call the func to update the color history

        self.eraserButton.config(state=ACTIVE) #set the eraser as active

    #eraser button callback
    def eraserFunc(self):
        self.currentColor = "#e8e9ed"
        self.eraserButton.config(state=DISABLED)  #since it's in use set it to disabled

    #clear button callback
    def clearFunc(self):
        self.canvas.delete("all") #deletes everything drawn in the canvas

    #changes the width, width scale callback
    def widthFunc(self, width):
        self.currentWidth = width

    #updates the color/swatch history with the new color just clicked
    def updateColorHistory(self, colors):
        cont = 0
        for widget in self.swatchFrame.winfo_children(): #destroy everything so we dont have repeating
            widget.destroy()
        
        for color in range(len(colors)): #add all the colors in the list
            blankBtn = Button(self.swatchFrame, text="", width=2, height=1, bg=colors[color], command=partial(self.swatchColor, colors[color])) #buttons so you can click them and it switches the color
            if color <= 5:
                blankBtn.grid(row=0, column=color)
            elif color >= 6 and color < 12: #making a second row
                blankBtn.grid(row=1, column=cont)
                cont+=1
        
        if len(colors) > 12: #if there are more than 12 swatched then we want the last one to change its color
            if self.colorIndex == 11:
                self.colorIndex = 0
            else:
                self.colorIndex+=1

            colors[self.colorIndex] = colors[-1] #make the recently selceted color the first one
            colors.pop() #remove the recently selected  color
            self.colorHistory = colors #update the list
            self.updateColorHistory(self.colorHistory) #then update the swatches thing again

    #when you click the swatch callback
    def swatchColor(self, colors):
        self.currentColor = colors
        self.eraserButton.config(state=ACTIVE)

    #adds the commands to the file menu
    def fileMenuCommands(self, menu):
        menu.add_command(label="Save Image", command=self.saveFile)
        menu.add_command(label="Animate", command=self.animate)
        menu.add_separator()
        menu.add_command(label="Quit", command=self.main.quit)

    #save the file    
    def saveFile(self, event=None):
        time = datetime.datetime.now()
        timeNow = time.strftime("%m-%d-%Y, %H-%M-%S")
        im = pg.screenshot(region=(168, 45, 1750, 830)) #takes a screen shot of the region (uhhh... postscript bad, me not smart)

        try: #dont know if i need this here, but yea
            im.save(f"savedImages/{timeNow}.png") #uses the time and motnth, etc. to set the name so it's always unique
        except Exception as _:
            self.initFolders()
            self.saveFile()

        #updates the pictures bar
        self.initPicturesBar(True)

    #compiles all the photos into a video using cv2 video writer
    def animate(self):
        time = datetime.datetime.now()
        timeNow = time.strftime("%m-%d-%Y, %H-%M-%S")
        vidName = "Animated "+str(timeNow)+".avi"
        images = [img for img in os.listdir(self.imageDir)] #gets all the images in the image directory
        frame = cv2.imread(os.path.join(self.imageDir, images[0])) #since the width, height is the same for all of them, we just get the first one (kind of a redundant step tbh now that im looking at it, could just hard code the width/height values)
        height, width, _ = frame.shape

        video = cv2.VideoWriter(self.completedDir+"\\"+vidName, 0, int(self.videoFrameRate), (width, height)) 

        for im in images:
            video.write(cv2.imread(os.path.join(self.imageDir, im))) #add the images to the video

        video.release()    #release it from jail 

    #deletes all the photos/frames from the folder
    def deleteAll(self):
        try: #again, dont know if i need this, i did this before the error even came up, so yea
            for im in os.listdir(self.imageDir): #go thru all the images
                path = os.path.join(self.imageDir, im)
                os.remove(path) #delete them sadge
            
            self.initPicturesBar(True) #refresh the pictures bar
        except Exception as _:
            print("No Files To Delete")

    #frame rate scale callback function, sets the frame rate to the frame rate on the scale
    def frameFunc(self, frame): 
        self.videoFrameRate = frame

#pog
if __name__ == '__main__':
    PaintApp()   
