from tkinter import *
import tkinter as tk
from tkinter import messagebox
#import tkinter as tk
from PIL import Image, ImageTk
from time import *
import RPi.GPIO as GPIO
import math
import os 
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

for x in range(1, 28):
  GPIO.setup(x, GPIO.OUT, initial=GPIO.HIGH)
  
  

####################### Root ########################################
#####################################################################
lock = 0

def findGPIONo(argument):
    switcher = {
        1:27,
        2:3,
        3:22,
        4:18,
        5:23,
        6:24,
        7:25,
    }
    return switcher.get(argument, " ")

def turnBgON(v):
    v["bg"] = "green"
    v["activebackground"] = "green"

def turnBgOFF (v):
    v["bg"] = "red"
    v["activebackground"] = "red"

def toggleBg(v):
    if v["bg"] == "red":
        turnBgON(v)
    else :
        turnBgOFF(v)

def checkLine(x):
    tp = GPIO.input(x)
    if tp ==1:
        return 0
    else:
        return 1

def turnLineON(x, v):
    GPIO.output(x, GPIO.LOW)
    turnBgON(v)

def turnLineOFF(x, v):
    GPIO.output(x, GPIO.HIGH)
    turnBgOFF(v)

def toggleLine(x, v):
    if checkLine(x):
        turnLineOFF(x, v)
    else:
        turnLineON(x, v)

def turnValveON(x,v,access):
    if lock == 0 or (lock==1 and access == 1) :
        pinNo = findGPIONo(x)
        turnLineON(pinNo, v)

def turnValveOFF(x, v,access):
    if lock == 0 or (lock==1 and access == 1) :
        pinNo = findGPIONo(x)
        turnLineOFF(pinNo, v)

def toggleValve(x, v,access):
    if lock == 0 or (lock==1 and access == 1) :
        pinNo = findGPIONo(x)
        toggleLine(pinNo, v)

def shutDown():
    for x in range(1, 27):
      GPIO.output(x, GPIO.LOW)

def manual_back(access):
    if access == 0:
        return
    back_take_access()
    lock_valve()
    start_countdown(6)
    turnValveOFF(6,V6,1)
    turnValveOFF(7,V7,1)
    manual_frame.after(5000, lambda:remaining())

def remaining():
    turnValveOFF(1,V1,1)
    turnValveOFF(2,V2,1)
    turnValveOFF(3,V3,1)
    turnValveOFF(4,V4,1)
    turnValveOFF(5,V5,1)
    manual_frame.after(1000, lambda:show_frame(main_frame))
    manual_frame.after(1000, back_give_acess)
    manual_frame.after(1000, unlock_valve)

    #GPIO.cleanup()
def unlock_valve():
    global lock
    lock = 0
def lock_valve():
    global lock
    lock =1
def back_give_acess():
    global back_access
    back_access = 1

def back_take_access():
    global back_access
    back_access = 0
back_access = 1
#####################################################################
#####################################################################


valve_interface=tk.Tk()

valve_interface.config(cursor = "none")
valve_interface.attributes('-fullscreen', True)

valve_interface.title("Valve Interface")
valve_interface.rowconfigure(0, weight = 1)
valve_interface.columnconfigure(0, weight = 1)
valve_interface.geometry('800x480')


def exitprog():
    checkVote = tk.messagebox.askquestion( "Exit", "Are you sure you want to Exit ?")
    if checkVote == 'yes':
        shutDown()
        #valve_interface.destroy()
        os.system("sudo shutdown -h now")
checkManInt = False

def show_frame(frame):
    frame.tkraise()

##################################Frame BASE####################################
################################################################################



main_frame = tk.Frame(valve_interface, bg = "black")
manual_frame = tk.Frame(valve_interface, bg = "black")
auto_frame = tk.Frame(valve_interface, bg = "black")
select_frame = tk.Frame(valve_interface, bg = "black")
manual_steps_frame = tk.Frame(valve_interface, bg = "black")
edit_frame = tk.Frame(valve_interface, bg = "black")

for frame in (main_frame, manual_frame, auto_frame, select_frame, manual_steps_frame, edit_frame):
    frame.grid(row=0, column=0, sticky='nsew')

########################################################################################
########################################################################################

######################### SELECT FRAME ##########################################
################################################################################

Sstartx = 0.063
Sstarty = 0.37
Smargin = 0.3

auto_button = tk.Button(select_frame, text="AUTO", command = lambda:start_auto(), width = 25, height  =11, relief="ridge", bg="yellow", activebackground="yellow")
auto_button.place(relx = Sstartx , rely= Sstarty)

msc_button = tk.Button(select_frame, text="MANUAL STEP \nCONTROL", command = lambda:show_frame(manual_steps_frame), width = 25, height  =11, relief="ridge", bg="yellow", activebackground="yellow")
msc_button.place(relx = Sstartx + Smargin , rely= Sstarty)

edit_button = tk.Button(select_frame, text="EDIT TIME", command = lambda:show_frame(edit_frame), width = 25, height  =11, relief="ridge", bg="yellow", activebackground="yellow")
edit_button.place(relx = Sstartx + 2*Smargin , rely= Sstarty)


select_back = tk.Button(select_frame, text= "Back", width = 10, height =1, relief = "ridge", bg ="white", activebackground="grey", command = lambda:show_frame(main_frame))
select_back.pack(side = "bottom" )
################################################################################
################################################################################


#########################AUTO FRAME PROCESSES############################################
#########################################################################################
x = [None]*20
t_fast_rinse = 60000
t_service = 3600000
t_back_wash = 60000
t_forward_wash = 60000

def start_auto():
    show_frame(auto_frame)
    pn.config(text = 'Ongoing process: Fast Rinse')
    x[0] = auto_frame.after(1000,lambda:fast_rinse())

def fast_rinse():
    pn.config(text = 'Ongoing process: Fast Rinse')
    turnValveON(2,v2,1)
    turnValveON(3,v3,1)
    x[1] = auto_frame.after(5000, lambda:turnValveON(6,v6,1))
    x[2] = auto_frame.after(5000 + t_fast_rinse, lambda:turnValveOFF(6,v6,1))
    x[3] = auto_frame.after(10000 + t_fast_rinse, lambda:turnValveOFF(2,v2,1))
    x[4] = auto_frame.after(10000 + t_fast_rinse, lambda:turnValveOFF(3,v3,1))
    x[5] = auto_frame.after(10000 + t_fast_rinse, lambda:service())

def service():
    pn.config(text = 'Ongoing process: Service')
    turnValveON(1,v1,1)
    turnValveON(5,v5,1)
    x[6] = auto_frame.after(5000, lambda:turnValveON(6,v6,1))
    x[7] = auto_frame.after(5000 + t_service, lambda:turnValveOFF(6,v6,1))
    x[8] = auto_frame.after(10000 + t_service, lambda:turnValveOFF(1,v1,1))
    x[9] = auto_frame.after(10000 + t_service, lambda:turnValveOFF(5,v5,1))
    x[10] = auto_frame.after(10000 + t_service, lambda:back_wash())

def back_wash():
    pn.config(text = 'Ongoing process: Back Wash')
    turnValveON(3,v3,1)
    x[11] = auto_frame.after(5000, lambda:turnValveON(7,v7,1))
    x[12] = auto_frame.after(5000 + t_back_wash, lambda:turnValveOFF(7,v7,1))
    x[13] = auto_frame.after(10000 + t_back_wash, lambda:turnValveOFF(3,v3,1))
    x[14] = auto_frame.after(10000 + t_back_wash, lambda:forward_wash())

def forward_wash():
    pn.config(text = 'Ongoing process: Forward Wash')
    turnValveON(1,v1,1)
    turnValveON(4,v4,1)
    x[15] = auto_frame.after(5000, lambda:turnValveON(6,v6,1))
    x[16] = auto_frame.after(5000 + t_forward_wash, lambda:turnValveOFF(6,v6,1))
    x[17] = auto_frame.after(10000 + t_forward_wash, lambda:turnValveON(5,v5,1))
    x[18] = auto_frame.after(15000 + t_forward_wash, lambda:turnValveOFF(4,v4,1))
    x[19] = auto_frame.after(15000 + t_forward_wash, lambda:service())


def auto_back(access):
    if access == 0:
        return
    back_take_access()
    for i in range(20):
        if x[i] != None:
            auto_frame.after_cancel(x[i])
            print(x[i])
            x[i] = None
    turnValveOFF(6,v6,1)
    turnValveOFF(7,v7,1)
    a_start_countdown(5)
    auto_frame.after(5000, ValveOFF)

def ValveOFF():
    turnValveOFF(1,v1,1)
    turnValveOFF(2,v2,1)
    turnValveOFF(3,v3,1)
    turnValveOFF(4,v4,1)
    turnValveOFF(5,v5,1)
    auto_frame.after(1, lambda:show_frame(select_frame))
    auto_frame.after(1000, back_give_acess)
###############################################################################
###############################################################################

########################Clock##################################################
###############################################################################


def time():
    string = strftime('%I:%M:%S %p\n %d/%m/%Y')
    clock.config(text = string)
    clock.after(1000, time)

def time1():
    string = strftime('%I:%M:%S %p\n %d/%m/%Y')
    clock1.config(text = string)
    clock1.after(1000, time1)

def time2():
    string = strftime('%I:%M:%S %p\n %d/%m/%Y')
    clock2.config(text = string)
    clock2.after(1000, time2)

def time3():
    string = strftime('%I:%M:%S %p\n %d/%m/%Y')
    clock3.config(text = string)
    clock3.after(1000, time3)

def time4():
    string = strftime('%I:%M:%S %p\n %d/%m/%Y')
    clock4.config(text = string)
    clock4.after(1000, time4)

clock = Label(main_frame, font = ('calibri', 20, 'bold'),bg = 'black',foreground = 'white')
clock.pack(anchor = 'ne')

clock1 = Label(manual_frame, font = ('calibri', 20, 'bold'),bg = 'black',foreground = 'white')
clock1.pack(anchor = 'ne')

clock2 = Label(auto_frame, font = ('calibri', 20, 'bold'),bg = 'black',foreground = 'white')
clock2.pack(anchor = 'ne')

clock3 = Label(select_frame, font = ('calibri', 20, 'bold'),bg = 'black',foreground = 'white')
clock3.pack(anchor = 'ne')

clock4 = Label(manual_steps_frame, font = ('calibri', 20, 'bold'),bg = 'black',foreground = 'white')
clock4.pack(anchor = 'ne')
################################################################################
################################################################################

################################MANUAL FRAME####################################
################################################################################
screen_width = valve_interface.winfo_screenwidth()
screen_height = valve_interface.winfo_screenheight()
vstartx = 0.15
vstartx2 = 0.05
vstarty = 0.22
vmargin = 0.2
vmarginy =0.55
vwidth = round(0.01*screen_width)
vheight = round(0.01*screen_height)

V1= tk.Button(manual_frame,text="Valve 1", command = lambda:toggleValve(1, V1, 0), width = vwidth, height  = vheight,relief="ridge", bg="red", activebackground="red")
V1.place(relx = vstartx, rely = vstarty)

V2 = tk.Button(manual_frame, text="Valve 2", command = lambda:toggleValve(2, V2, 0) ,width = vwidth, height  = vheight, relief="ridge", bg="red", activebackground="red")
V2.place(relx = vstartx + vmargin, rely = vstarty)

V3= tk.Button(manual_frame,text="Valve 3", command = lambda:toggleValve(3, V3, 0), width = vwidth, height  = vheight,relief="ridge", bg="red", activebackground="red")
V3.place(relx = vstartx + 2*vmargin, rely = vstarty)

V4 = tk.Button(manual_frame, text="Valve 4", command = lambda:toggleValve(4, V4, 0), width = vwidth, height  = vheight, relief="ridge", bg="red", activebackground="red")
V4.place(relx = vstartx + 3*vmargin, rely= vstarty)

V5 = tk.Button(manual_frame,text="Valve 5", command = lambda:toggleValve(5, V5, 0), width = vwidth, height  = vheight,relief="ridge", bg="red", activebackground="red")
V5.place(relx = vstartx2 + vmargin, rely= vmarginy)

V6 = tk.Button(manual_frame, text="Pump 1", command = lambda:toggleValve(6, V6, 0), width = vwidth, height  = vheight, relief="ridge", bg="red", activebackground="red")
V6.place(relx = vstartx2 + 2*vmargin, rely= vmarginy)

V7 = tk.Button(manual_frame,text="Pump 2", command = lambda:toggleValve(7, V7, 0), width = vwidth, height  = vheight,relief="ridge", bg="red", activebackground="red")
V7.place(relx = vstartx2 + 3*vmargin, rely= vmarginy)

VBack = tk.Button(manual_frame, text= "Back", width = 10, height =1, relief = "ridge", bg ="white", activebackground="grey", command = lambda:manual_back(back_access) )
VBack.pack(side = "bottom" )

def start_countdown(count):
    if(count == 0):
        countdown.config(text = "")
        return "back"
    countdown.config(text = "Closing in " +str(count)+"s")
    manual_frame.after(1000, lambda:start_countdown(count - 1))

countdown = Label(manual_frame, font = ('calibri', 25, 'bold'), bg = 'black', foreground ='white')
countdown.place(relx = 0, rely = 0)
################################################################################
################################################################################


########################### AUTO FRAME #########################################
################################################################################

pn = Label(auto_frame, font = ('calibri', 25, 'bold'),bg = 'black',foreground = 'white')
pn.place(anchor = 'nw')

v1 = tk.Label(auto_frame,text="Valve 1", width = vwidth, height  = vheight,relief="ridge", bg="red", activebackground="yellow")
v1.place(relx = vstartx, rely = vstarty)

v2 = tk.Label(auto_frame, text="Valve 2", width = vwidth, height  = vheight, relief="ridge", bg="red", activebackground="yellow")
v2.place(relx = vstartx + vmargin, rely = vstarty)

v3 = tk.Label(auto_frame,text="Valve 3", width = vwidth, height  = vheight,relief="ridge", bg="red", activebackground="yellow")
v3.place(relx = vstartx + 2*vmargin, rely = vstarty)

v4 = tk.Label(auto_frame, text="Valve 4", width = vwidth, height  = vheight, relief="ridge", bg="red", activebackground="yellow")
v4.place(relx = vstartx + 3*vmargin, rely= vstarty)

v5 = tk.Label(auto_frame,text="Valve 5", width = vwidth, height  = vheight,relief="ridge", bg="red", activebackground="yellow")
v5.place(relx = vstartx2 + vmargin, rely= vmarginy)

v6 = tk.Label(auto_frame, text="Pump 1", width = vwidth, height  = vheight, relief="ridge", bg="red", activebackground="yellow")
v6.place(relx = vstartx2 + 2*vmargin, rely= vmarginy)

v7 = tk.Label(auto_frame,text="Pump 2", width = vwidth, height  = vheight,relief="ridge", bg="red", activebackground="yellow")
v7.place(relx = vstartx2 + 3*vmargin, rely= vmarginy)

def a_start_countdown(count):
    if(count == 0):
        pn.config(text = "")
        return "back"
    pn.config(text = "Closing in " +str(count)+"s")
    auto_frame.after(1000, lambda:a_start_countdown(count - 1))


ABack = tk.Button(auto_frame, text= "Back", width = 10, height =1, relief = "ridge", bg ="white", activebackground="grey", command = lambda:auto_back(back_access))
ABack.pack(side = "bottom" )

###########################################################################################################################
###########################################################################################################################


###################################################EDIT FRAME#######################################################
###########################################################################################################################


stepx = 0.3
stepy = 0.13
xstepx = 0.05


curr_button = None


def edit_time(x,y):
    tp = y["text"]
    tp = tp + str(x)
    y.config(text = tp)

edit = 0

def find_edit(x):
    x["text"] = ""
    global curr_button
    if x != curr_button:
        if curr_button != None and curr_button["text"] == "":
            curr_button["text"] = "0"
        curr_button = x
    global edit
    edit = x

e_fast_rinse = Label(edit_frame, text = " FAST RINSE :", fg = "red" , font = ('Arial', 15, 'bold'), bg = "black")
e_fast_rinse.place(relx = xstepx, rely = stepy)

e_service = Label(edit_frame, text = "SERVICE :", fg = "red" , font = ('Arial', 15, 'bold'), bg = "black")
e_service.place(relx = xstepx, rely = stepy*2)

e_back_wash = Label(edit_frame, text = "BACK WASH :", fg = "red" , font = ('Arial', 15, 'bold'), bg = "black")
e_back_wash.place(relx = xstepx, rely = stepy*3)

e_forward_wash = Label(edit_frame, text = "FORWARD WASH :", fg = "red" , font = ('Arial', 15, 'bold'), bg = "black")
e_forward_wash.place(relx = xstepx, rely = stepy*4)

hr_label = Label(edit_frame, width = 5, text = "HR")
hr_label.place(relx = stepx*1.06, rely = stepy*0.5)

m_label = Label(edit_frame, width = 5,text = "M")
m_label.place(relx = stepx*1.36, rely = stepy*0.5)

s_label = Label(edit_frame, width = 5, text = "S")
s_label.place(relx = stepx*1.66, rely = stepy*0.5)

def find_hours(t):
    return math.floor(t/3600)

def find_minutes(t):
    return math.floor((t - find_hours(t)*3600)/60)

def find_seconds(t):
    return math.floor((t - find_hours(t)*3600 - find_minutes(t)*60))

hr_fast_rinse = Button(edit_frame, width = 5, text = str(find_hours(t_fast_rinse/1000)), relief = 'solid', command = lambda:find_edit(hr_fast_rinse))
hr_fast_rinse.place(relx = stepx, rely = stepy)

m_fast_rinse = Button(edit_frame, width = 5, text = str(find_minutes(t_fast_rinse/1000)),  command = lambda:find_edit(m_fast_rinse),  relief = 'solid')
m_fast_rinse.place(relx = stepx*1.3, rely = stepy)

s_fast_rinse = Button(edit_frame, width = 5, text = str(find_seconds(t_fast_rinse/1000)), command = lambda:find_edit(s_fast_rinse),  relief = 'solid')
s_fast_rinse.place(relx = stepx*1.6, rely = stepy)


hr_service = Button(edit_frame, width = 5,  text = str(find_hours(t_service/1000)), command = lambda:find_edit(hr_service), relief = 'solid')
hr_service.place(relx = stepx, rely = stepy*2)

m_service = Button(edit_frame, width = 5, text = str(find_minutes(t_service/1000)), command = lambda:find_edit(m_service), relief = 'solid')
m_service.place(relx = stepx*1.3, rely = stepy*2)

s_service = Button(edit_frame, width = 5, text = str(find_seconds(t_service/1000)), command = lambda:find_edit(s_service), relief = 'solid')
s_service.place(relx = stepx*1.6, rely = stepy*2)


hr_back_wash = Button(edit_frame, width = 5, text = str(find_hours(t_back_wash/1000)), command = lambda:find_edit(hr_back_wash), relief = 'solid')
hr_back_wash.place(relx = stepx, rely = stepy*3)

m_back_wash = Button(edit_frame, width = 5, text = str(find_minutes(t_back_wash/1000)), command = lambda:find_edit(m_back_wash), relief = 'solid')
m_back_wash.place(relx = stepx*1.3, rely = stepy*3)

s_back_wash = Button(edit_frame, width = 5, text = str(find_seconds(t_back_wash/1000)),command = lambda:find_edit(s_back_wash), relief = 'solid')
s_back_wash.place(relx = stepx*1.6, rely = stepy*3)


hr_forward_wash = Button(edit_frame, width = 5, text = str(find_hours(t_forward_wash/1000)), command = lambda:find_edit(hr_forward_wash), relief = 'solid')
hr_forward_wash.place(relx = stepx, rely = stepy*4)

m_forward_wash = Button(edit_frame, width = 5, text = str(find_minutes(t_forward_wash/1000)), command = lambda:find_edit(m_forward_wash), relief = 'solid')
m_forward_wash.place(relx = stepx*1.3, rely = stepy*4)

s_forward_wash = Button(edit_frame, width = 5, text = str(find_seconds(t_forward_wash/1000)),command = lambda:find_edit(s_forward_wash), relief = 'solid')
s_forward_wash.place(relx = stepx*1.6, rely = stepy*4)



apply_button = Button(edit_frame, text = "APPLY", height = 1, width = 6, bg = "yellow", command = lambda:update_time())
apply_button.place(relx = 1.05*stepx, rely = stepy*5)

reset_button = Button(edit_frame, text = "RESET", height = 1, width = 6, bg = "yellow", command = lambda:reset_time())
reset_button.place(relx = 1.4*stepx, rely = stepy*5)



def update_time():
    global t_fast_rinse
    global t_service
    global t_back_wash
    global t_forward_wash

    checkVote = tk.messagebox.askquestion( "Warning", "Do you really wish to change the time intervals ?")
    if checkVote == 'yes':
        t_fast_rinse = (3600*int(hr_fast_rinse["text"]) + 60*int(m_fast_rinse["text"]) + int(s_fast_rinse["text"]))*1000
        t_service = (3600*int(hr_service["text"]) + 60*int(m_service["text"]) + int(s_service["text"]))*1000
        t_back_wash = (3600*int(hr_back_wash["text"]) + 60*int(m_back_wash["text"]) + int(s_back_wash["text"]))*1000
        t_forward_wash = (3600*int(hr_forward_wash["text"]) + 60*int(m_forward_wash["text"]) + int(s_forward_wash["text"]))*1000
        tk.messagebox.showinfo("Update", "Time intervals are updated")
        print(t_fast_rinse)
        print(t_service)
        print(t_back_wash)
        print(t_forward_wash)
    else:
        hr_fast_rinse.config(text = str(find_hours(t_fast_rinse/1000)))
        m_fast_rinse.config(text = str(find_minutes(t_fast_rinse/1000)))
        s_fast_rinse.config(text = str(find_seconds(t_fast_rinse/1000)))

        hr_service.config(text = str(find_hours(t_service/1000)))
        m_service.config(text = str(find_minutes(t_service/1000)))
        s_service.config(text = str(find_seconds(t_service/1000)))

        hr_back_wash.config(text = str(find_hours(t_back_wash/1000)))
        m_back_wash.config(text = str(find_minutes(t_back_wash/1000)))
        s_back_wash.config(text = str(find_seconds(t_back_wash/1000)))

        hr_forward_wash.config(text = str(find_hours(t_forward_wash/1000)))
        m_forward_wash.config(text = str(find_minutes(t_forward_wash/1000)))
        s_forward_wash.config(text = str(find_seconds(t_forward_wash/1000)))
def reset_time():
    global t_fast_rinse
    global t_service
    global t_back_wash
    global t_forward_wash

    t_fast_rinse = 60000
    t_service = 3600000
    t_back_wash = 60000
    t_forward_wash = 60000

    hr_fast_rinse.config(text = str(find_hours(t_fast_rinse/1000)))
    m_fast_rinse.config(text = str(find_minutes(t_fast_rinse/1000)))
    s_fast_rinse.config(text = str(find_seconds(t_fast_rinse/1000)))

    hr_service.config(text = str(find_hours(t_service/1000)))
    m_service.config(text = str(find_minutes(t_service/1000)))
    s_service.config(text = str(find_seconds(t_service/1000)))

    hr_back_wash.config(text = str(find_hours(t_back_wash/1000)))
    m_back_wash.config(text = str(find_minutes(t_back_wash/1000)))
    s_back_wash.config(text = str(find_seconds(t_back_wash/1000)))

    hr_forward_wash.config(text = str(find_hours(t_forward_wash/1000)))
    m_forward_wash.config(text = str(find_minutes(t_forward_wash/1000)))
    s_forward_wash.config(text = str(find_seconds(t_forward_wash/1000)))

    checkVote = tk.messagebox.showinfo( "Reset", "The Time intervals are resetted")

    print(t_service)
    print(t_back_wash)
    print(t_forward_wash)

numpad = [None]*10

numpad[1] = Button(edit_frame, text = str(1), height = 1, width = 6, bg = "yellow", command = lambda:edit_time(1,edit), activebackground = "yellow")
numpad[1].place(relx = stepx*2.1, rely = stepy)

numpad[2] = Button(edit_frame, text = str(2), height = 1, width = 6, bg = "yellow", command = lambda:edit_time(2,edit), activebackground = "yellow")
numpad[2].place(relx = stepx*2.5, rely = stepy)

numpad[3] = Button(edit_frame, text = str(3), height = 1, width = 6, bg = "yellow", command = lambda:edit_time(3,edit), activebackground = "yellow")
numpad[3].place(relx = stepx*2.9, rely = stepy)

numpad[4] = Button(edit_frame, text = str(4), height = 1, width = 6, bg = "yellow", command = lambda:edit_time(4,edit), activebackground = "yellow")
numpad[4].place(relx = stepx*2.1, rely = stepy*2)

numpad[5] = Button(edit_frame, text = str(5), height = 1, width = 6, bg = "yellow", command = lambda:edit_time(5,edit), activebackground = "yellow")
numpad[5].place(relx = stepx*2.5, rely = stepy*2)

numpad[6] = Button(edit_frame, text = str(6), height = 1, width = 6, bg = "yellow", command = lambda:edit_time(6,edit), activebackground = "yellow")
numpad[6].place(relx = stepx*2.9, rely = stepy*2)

numpad[7] = Button(edit_frame, text = str(7), height = 1, width = 6, bg = "yellow", command = lambda:edit_time(7,edit), activebackground = "yellow")
numpad[7].place(relx = stepx*2.1, rely = stepy*3)

numpad[8] = Button(edit_frame, text = str(8), height = 1, width = 6, bg = "yellow", command = lambda:edit_time(8,edit), activebackground = "yellow")
numpad[8].place(relx = stepx*2.5, rely = stepy*3)

numpad[9] = Button(edit_frame, text = str(9), height = 1, width = 6, bg = "yellow", command = lambda:edit_time(9,edit), activebackground = "yellow")
numpad[9].place(relx = stepx*2.9, rely = stepy*3)

numpad[0] = Button(edit_frame, text = str(0), height = 1, width = 6, bg = "yellow", command = lambda:edit_time(0,edit), activebackground = "yellow")
numpad[0].place(relx = stepx*2.5, rely = stepy*4)

edit_back = Button(edit_frame, text= "Back", width = 10, height =1, relief = "ridge", bg ="white", activebackground="grey", command = lambda:edit_back_p() )
edit_back.pack(side = "bottom" )

def edit_back_p():
    global t_fast_rinse
    global t_service
    global t_back_wash
    global t_forward_wash
    checkVote = tk.messagebox.askquestion( "warning", "Do you wish to save the time intervals ?")
    if checkVote == 'yes' :
        t_fast_rinse = (3600*int(hr_fast_rinse["text"]) + 60*int(m_fast_rinse["text"]) + int(s_fast_rinse["text"]))*1000
        t_service = (3600*int(hr_service["text"]) + 60*int(m_service["text"]) + int(s_service["text"]))*1000
        t_back_wash = (3600*int(hr_back_wash["text"]) + 60*int(m_back_wash["text"]) + int(s_back_wash["text"]))*1000
        t_forward_wash = (3600*int(hr_forward_wash["text"]) + 60*int(m_forward_wash["text"]) + int(s_forward_wash["text"]))*1000
        print(t_fast_rinse)
        print(t_service)
        print(t_back_wash)
        print(t_forward_wash)
        show_frame(select_frame)
    else :
        hr_fast_rinse.config(text = str(find_hours(t_fast_rinse/1000)))
        m_fast_rinse.config(text = str(find_minutes(t_fast_rinse/1000)))
        s_fast_rinse.config(text = str(find_seconds(t_fast_rinse/1000)))

        hr_service.config(text = str(find_hours(t_service/1000)))
        m_service.config(text = str(find_minutes(t_service/1000)))
        s_service.config(text = str(find_seconds(t_service/1000)))

        hr_back_wash.config(text = str(find_hours(t_back_wash/1000)))
        m_back_wash.config(text = str(find_minutes(t_back_wash/1000)))
        s_back_wash.config(text = str(find_seconds(t_back_wash/1000)))

        hr_forward_wash.config(text = str(find_hours(t_forward_wash/1000)))
        m_forward_wash.config(text = str(find_minutes(t_forward_wash/1000)))
        s_forward_wash.config(text = str(find_seconds(t_forward_wash/1000)))
        show_frame(select_frame)

        
###############################################################################################################################
###############################################################################################################################

#######################################################MANUAL STEP FRAME########################################################################
###############################################################################################################################
msc_fast_rinse_check = 0
msc_service_check = 0
msc_back_wash_check = 0
msc_forward_wash_check = 0

ongoing_process = 0

msc_lock = 0


process_access = 1

def process_take_access():
    global process_access
    process_access = 0

def process_give_access():
    global process_access
    process_access = 1

def msc_start_countdown(count):
    if(count == 0):
        msc_countdown.config(text = "")
        return "back"
    msc_countdown.config(text =str(count))
    manual_steps_frame.after(1000, lambda:msc_start_countdown(count - 1))

msc_countdown = Label(manual_steps_frame, font = ('calibri', 25, 'bold'), bg = 'black', foreground ='white')
msc_countdown.pack(anchor = 'se')

def startprocess(x,y):
    global msc_lock
    global ongoing_process
    if x==1:
        if y == 1:
            msc_pn.config(text = 'Ongoing Process: Fast Rinse')
            msc_fast_rinse["bg"] = "green"
            msc_fast_rinse["activebackground"] = "green"
            process_give_access()
            msc_lock = 0

        else:
            msc_pn.config(text = '')
            msc_fast_rinse["bg"] = "red"
            msc_fast_rinse["activebackground"] = "red"
            process_give_access()
            ongoing_process = 0
            msc_lock = 0
    elif x ==2:
        if y == 1:
            msc_pn.config(text = 'Ongoing Process: Service')
            msc_service["bg"] = "green"
            msc_service["activebackground"] = "green"
            process_give_access()
            msc_lock = 0
        else:
            msc_pn.config(text = '')
            msc_service["bg"] = "red"
            msc_service["activebackground"] = "red"
            process_give_access()
            ongoing_process = 0
            msc_lock = 0
    elif x == 3:
        if y == 1:
            msc_pn.config(text = 'Ongoing Process: Back Wash')
            msc_back_wash["bg"] = "green"
            msc_back_wash["activebackground"] = "green"
            process_give_access()
            msc_lock = 0
        else:
            msc_pn.config(text = '')
            msc_back_wash["bg"] = "red"
            msc_back_wash["activebackground"] = "red"
            process_give_access()
            ongoing_process = 0
            msc_lock = 0
    elif x == 4:
        if y == 1:
            msc_pn.config(text = 'Ongoing Process: Forward Wash')
            msc_forward_wash["bg"] = "green"
            msc_forward_wash["activebackground"] = "green"
            process_give_access()
            msc_lock = 0
        else:
            msc_pn.config(text = '')
            msc_forward_wash["bg"] = "red"
            msc_forward_wash["activebackground"] = "red"
            process_give_access()
            ongoing_process = 0
            msc_lock = 0
def msc_fast_rinse_p(access):
    global msc_lock
    global ongoing_process
    if ongoing_process==0:
        msc_pn.config(text = 'Starting Process: Fast Rinse')
        msc_start_countdown(5)
        ongoing_process = 1
        msc_lock = 1
        msc_fast_rinse["bg"] = "orange"
        msc_fast_rinse["activebackground"] = "orange"
        turnValveON(2,v2,1)
        turnValveON(3,v3,1)
        process_take_access()
        manual_steps_frame.after(5000, lambda:turnValveON(6,v6,1))
        manual_steps_frame.after(5000, lambda:startprocess(1,1))
    elif ongoing_process == 1:
        if access == 0:
            return
        msc_pn.config(text = 'Closing Process: Fast Rinse')
        msc_start_countdown(5)
        msc_fast_rinse["bg"] = "orange"
        msc_fast_rinse["activebackground"] = "orange"
        turnValveOFF(6,v6,1)
        process_take_access()
        msc_lock = 1
        manual_steps_frame.after(5000 , lambda:turnValveOFF(2,v2,1))
        manual_steps_frame.after(5000 , lambda:turnValveOFF(3,v3,1))
        manual_steps_frame.after(5000, lambda:startprocess(1,0))
def msc_service_p(access):
    global msc_lock
    global ongoing_process
    if ongoing_process == 0:
        msc_pn.config(text = 'Starting process: Service')
        msc_start_countdown(5)
        ongoing_process = 2
        msc_service["bg"] = "orange"
        msc_service["activebackground"] = "orange"
        turnValveON(1,v1,1)
        turnValveON(5,v5,1)
        process_take_access()
        msc_lock = 1
        manual_steps_frame.after(5000, lambda:turnValveON(6,v6,1))
        manual_steps_frame.after(5000, lambda:startprocess(2,1))
    elif ongoing_process == 2:
        if access == 0:
            return
        msc_pn.config(text = 'Closing Process: Service')
        msc_start_countdown(5)
        msc_service["bg"] = "orange"
        msc_service["activebackground"] = "orange"
        turnValveOFF(6,v6,1)
        process_take_access()
        msc_lock = 1
        manual_steps_frame.after(5000, lambda:turnValveOFF(1,v1,1))
        manual_steps_frame.after(5000, lambda:turnValveOFF(5,v5,1))
        manual_steps_frame.after(5000, lambda:startprocess(2,0))

def msc_back_wash_p(access):
    global msc_lock
    global ongoing_process
    if ongoing_process == 0:
        msc_pn.config(text = 'Starting process: Back Wash')
        msc_start_countdown(5)
        ongoing_process = 3
        msc_back_wash["bg"] = "orange"
        msc_back_wash["activebackground"] = "orange"
        turnValveON(3,v3,1)
        process_take_access()
        msc_lock = 1
        manual_steps_frame.after(5000, lambda:turnValveON(7,v7,1))
        manual_steps_frame.after(5000, lambda:startprocess(3,1))
    elif ongoing_process == 3:
        if access == 0:
            return
        msc_pn.config(text = 'Closing Process: Back Rinse')
        msc_start_countdown(5)
        msc_back_wash["bg"] = "orange"
        msc_back_wash["activebackground"] = "orange"
        turnValveOFF(7,v7,1)
        process_take_access()
        msc_lock = 1
        manual_steps_frame.after(5000, lambda:turnValveOFF(3,v3,1))
        manual_steps_frame.after(5000, lambda:startprocess(3,0))

def msc_forward_wash_p(access):
    global msc_lock
    global ongoing_process
    if ongoing_process ==0:
        msc_pn.config(text = 'Starting process: Forward Wash')
        msc_start_countdown(5)
        ongoing_process = 4
        msc_forward_wash["bg"] = "orange"
        msc_forward_wash["activebackground"] = "orange"
        turnValveON(1,v1,1)
        turnValveON(4,v4,1)
        process_take_access()
        msc_lock = 1
        manual_steps_frame.after(5000, lambda:turnValveON(6,v6,1))
        manual_steps_frame.after(5000, lambda:startprocess(4,1))
    elif ongoing_process == 4:
        if access == 0:
            return
        msc_pn.config(text = 'Closing Process: Forward Wash')
        msc_start_countdown(5)
        msc_forward_wash["bg"] = "orange"
        msc_forward_wash["activebackground"] = "orange"
        turnValveOFF(6,v6,1)
        process_take_access()
        msc_lock = 1
        manual_steps_frame.after(5000, lambda:turnValveOFF(4,v4,1))
        manual_steps_frame.after(5000, lambda:turnValveOFF(1,v1,1))
        manual_steps_frame.after(5000, lambda:startprocess(4,0))

def msc_back_p():
    global msc_lock
    global ongoing_process
    if msc_lock == 1:
        tk.messagebox.showinfo( "Warning", "Wait for the process to finish")
    else:
        if ongoing_process == 1:
            msc_fast_rinse_p(process_access)
            manual_steps_frame.after(5000, lambda:show_frame(select_frame))
        elif ongoing_process == 2:
            msc_service_p(process_access)
            manual_steps_frame.after(5000, lambda:show_frame(select_frame))
        elif ongoing_process == 3:
            msc_back_wash_p(process_access)
            manual_steps_frame.after(5000, lambda:show_frame(select_frame))
        elif ongoing_process == 4:
            msc_forward_wash_p(process_access)
            manual_steps_frame.after(5000, lambda:show_frame(select_frame))
        elif ongoing_process == 0:
            show_frame(select_frame)

mscx = 0.4
mscy = 0.15
xmscx = 0.2
screen_width = manual_steps_frame.winfo_screenwidth()
screen_height = manual_steps_frame.winfo_screenheight()

mscwidth = round(0.05*screen_width)
mscheight = round(0.005*screen_height)

msc_pn = Label(manual_steps_frame, font = ('calibri', 25, 'bold'),bg = 'black',foreground = 'white')
msc_pn.place(anchor = 'nw')

msc_fast_rinse = Button(manual_steps_frame, text = " FAST RINSE", height = mscheight , width = mscwidth, bg = 'red', activebackground = 'red', command= lambda:msc_fast_rinse_p(process_access), font = ('Arial', 15 , 'bold'))
msc_fast_rinse.place(relx = xmscx, rely = mscy)

msc_service = Button(manual_steps_frame, text = "SERVICE", height = mscheight , width = mscwidth, bg = 'red', activebackground = 'red', command= lambda:msc_service_p(process_access), font = ('Arial', 15 , 'bold'))
msc_service.place(relx = xmscx, rely = mscy*2.3)

msc_back_wash = Button(manual_steps_frame, text = "BACK WASH", height = mscheight , width = mscwidth, bg = 'red', activebackground = 'red', command= lambda:msc_back_wash_p(process_access), font = ('Arial', 15 , 'bold'))
msc_back_wash.place(relx = xmscx, rely = mscy*3.5)

msc_forward_wash = Button(manual_steps_frame, text = "FORWARD WASH", height = mscheight , width = mscwidth, bg = 'red', activebackground = 'red', command= lambda:msc_forward_wash_p(process_access), font = ('Arial', 15 , 'bold'))
msc_forward_wash.place(relx = xmscx, rely = mscy*4.8)

msc_back = Button(manual_steps_frame, text= "Back", width = 10, height =1, relief = "ridge", bg ="white", activebackground="grey", command = msc_back_p )
msc_back.pack(side = "bottom" )


###############################################################################################################################
###############################################################################################################################



########################## MAIN FRAME #####################################################################################
###########################################################################################################################
startx = 0.063
starty = 0.37
margin = 0.3

manual_button = tk.Button(main_frame,text="MANUAL", width = 25, command = lambda:show_frame(manual_frame),height  =11,relief="ridge", bg="yellow", activebackground="yellow")
manual_button.place(relx = startx, rely= starty)

auto_button = tk.Button(main_frame, text="AUTO", command = lambda:show_frame(select_frame), width = 25, height  =11, relief="ridge", bg="yellow", activebackground="yellow")
auto_button.place(relx = startx + margin, rely= starty)


exit_button = tk.Button(main_frame, text="EXIT", width = 25, height  =11, command = exitprog ,relief="ridge", bg="yellow", activebackground="yellow")
exit_button.place(relx = startx + 2*margin, rely= starty)
########################################################################################################################
########################################################################################################################


time()
time1 ()
time2 ()
time3()
time4()
show_frame(main_frame)

valve_interface.mainloop()
  