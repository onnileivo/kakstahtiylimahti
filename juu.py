import tkinter as tk
from matplotlib.backend_bases import key_press_handler
import numpy as np
import scipy.interpolate as spi
import scipy.integrate as spig


import scipy as sp
from scipy import constants

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)

import math

root = tk.Tk()
root.title("2strokaa")

ROWS = 5
COLS = 2

tkwidths = []
tkheights = []

cells = []

for c in range(COLS):
    col = []
    for r in range(ROWS):
        e = tk.Entry(root, width=15, font=("Aerial", 16))
        e.grid(row=r, column=c, ipadx=5, ipady=8)
        
        col.append(e.get)  
    cells.append(col)



def angle_from_x_after_tdc(x_target, tol=1e-6):
    low = 0.0
    high = 180.0

    while high - low > tol:
        mid = 0.5 * (low + high)
        if distFromTDC(mid) < x_target:
            low = mid
        else:
            high = mid

    return 0.5 * (low + high)


def angle_from_x_after_bdc(x_target, tol=1e-6):
    low = 180.0
    high = 360.0

    while high - low > tol:
        mid = 0.5 * (low + high)
        if distFromTDC(mid) > x_target:
            low = mid
        else:
            high = mid

    return 0.5 * (low + high)



def angle_from_bx_after_tdc(x_target, tol=1e-6):
    low = 0.0
    high = 180.0

    while high - low > tol:
        mid = 0.5 * (low + high)
        if distFromBDC(mid) > x_target:
            low = mid
        else:
            high = mid

    return 0.5 * (low + high)


def angle_from_bx_after_bdc(x_target, tol=1e-6):
    low = 180.0
    high = 360.0

    while high - low > tol:
        mid = 0.5 * (low + high)
        if distFromBDC(mid) < x_target:
            low = mid
        else:
            high = mid

    return 0.5 * (low + high)

def distFromTDC(angle) -> float:
    a = np.deg2rad(angle)
    Lct = stroke/2 # crank throw
    Lcr = conrod
    return Lcr + Lct * (1-np.cos(a)) - np.sqrt(Lcr ** 2 - np.pow(Lct * np.sin(a), 2))

def distFromBDC(angle) -> float:
    tdc = distFromTDC(angle)
    bdc = -tdc + stroke
    return bdc

def update_data(data, port: Port) :
    tkheights = data[0]
    tkwidths = data[1]
    port.port_heights = tkheights
    port.port_widths  = tkwidths
    fig.clear()
    port.plot()

class Port: #juuuuuuuuuu FAAAH NOT USED, better to have simpler ports fuck math
    port_heights = []
    port_widths = []
    port_timing = None
    port_interp = None
    def __init__(self, heights, widths, timing):
        self.port_heights = heights
        self.port_widths = widths # vois olla erikseen heights ja widhts jossai vec2 ja sitte mistä se portti oikeesti alkaa tiäkkö 
        self.port_timing = timing
        self.port_interp = spi.PchipInterpolator(heights, widths)

    def time_area():
        pass
        
    
    def height_area(self, height):
        return 2*spig.quad(self.port_interp, self.port_heights[0]-height, self.port_heights[0])
        

    def plot(self):
        plt.plot([-self.port_widths[0]/2, self.port_widths[0]/2], [self.port_heights[0],self.port_heights[0]])
        plt.plot(self.port_widths/2, self.port_heights)
        x=np.linspace(self.port_heights[0], self.port_heights[-1])
        plt.plot(self.port_interp(x)/2, x)
        plt.plot(-self.port_widths/2, self.port_heights)
        plt.plot([-self.port_widths[-1]/2, self.port_widths[-1]/2], [self.port_heights[-1],self.port_heights[-1]])


def swept_volume_mm():
    return (np.pi/4) * bore**2 * stroke
def swept_volume():
    return swept_volume_mm() * constants.milli ** 3


class SquarePort:
    def port_width(self, x0: float, xp : float, rt :float, rb :float, x01 :float, x02 :float) -> float:
        if x0 < x01 or x0 > x02:
            return 0
        if x0 < rt + x01:
            rooted = rt ** 2 - (rt - x0 + x01) ** 2
            if rooted < 0:
                rooted = 0
            return xp - 2*rt + 2 * np.sqrt(rooted)
        if x0 >= rt + x01 and x0 < x02 - rb:
            return xp
        if x0 > x01 - rb:
            rooted = rb ** 2 - (rb - x02 + x0) ** 2
            if rooted < 0:
                rooted = 0
            return xp - 2*rb + 2 * np.sqrt(rooted)
        print("wtf")
        return 0
    
    def port_area(self, x0, xp, rt, rb, x01, x02):
        width = lambda x: self.port_width(x, xp, rt, rb, x01, x02)
        y, _ = spig.quad(width, x01, x0)
        return y
    def time_area_abovepiston(self, xp, rt, rb, x01, x02, rpm):
        area = lambda x: self.areaThetaAbovePiston(x, xp, rt, rb, x01, x02) * 6 / rpm * constants.milli ** 2
        a, _ = spig.quad(area, angle_from_x_after_tdc(x01), angle_from_x_after_tdc(x02))
        return a
    
    def angle_area_abovepiston(self, xp, rt, rb, x01, x02):
        area = lambda x: self.areaThetaAbovePiston(x, xp, rt, rb, x01, x02) * constants.milli ** 2# mm^2 to m^2
        a, _ = spig.quad(area, angle_from_x_after_tdc(x01), angle_from_x_after_tdc(x02))
        return a
    
    def sta_abovepiston(self, xp, rt, rb, x01, x02, rpm):
        return self.time_area_abovepiston(xp,rt,rb,x01,x02,rpm)/swept_volume()
    
    def areaThetaAbovePiston(self, angle, xp, rt, rb, x01, x02):
        return self.port_area(distFromTDC(angle), xp, rt, rb, x01, x02)
    
    
    ## BELOW
    def areaThetaBelowPiston(self, angle, xp, rt, rb, x01, x02):
        return self.port_area(distFromBDC(angle), xp, rt, rb, x01, x02)
    
    def time_area_belowpiston(self, xp, rt, rb, x01, x02, rpm): # X01 ja X02 VOIDAAN MITATA MÄNNÄN PÄÄLTÄ, OIS HELPOMPAA
        area = lambda x: self.areaThetaBelowPiston(x, xp, rt, rb, x01, x02) * 6 / rpm * constants.milli ** 2
        a, _ = spig.quad(area, angle_from_bx_after_bdc(x01), angle_from_bx_after_bdc(x02))
        return a
    
    def angle_area_belowpiston(self, xp, rt, rb, x01, x02):
        area = lambda x: self.areaThetaBelowPiston(x, xp, rt, rb, x01, x02) * constants.milli ** 2# mm^2 to m^2
        a, _ = spig.quad(area, angle_from_bx_after_bdc(x01), angle_from_bx_after_bdc(x02))
        return a
    
    def sta_belowpiston(self, xp, rt, rb, x01, x02, rpm):
        return self.time_area_belowpiston(xp,rt,rb,x01,x02,rpm)/swept_volume()
    
    
    def getWidths(self, xp, rt, rb, x01, x02):
        x = np.linspace(x01, x02)
        y = [self.port_width(x0, xp, rt, rb, x01, x02) for x0 in x]
        return np.array(y)
    
    def plot(self, ax, widths, x01, x02, xoffset = 0):
        ax.yaxis.set_inverted(True)
        x = np.linspace(x01, x02, num=50)
        ax.plot([-widths[0]/2 +xoffset, widths[0]/2] +xoffset, [x01,x01])
        ax.plot([widths[-1]/2 + xoffset, -widths[-1]/2] +xoffset, [x02,x02])
        ax.plot(widths/2 +xoffset, x)
        ax.plot(-widths/2 +xoffset, x)
    # MISC SLOP 
    # mmm good slop
    """/
    def time_area_goofyway(self, xp, rt, rb, x01, x02, rpm): # the same im god's chosen programmer RAAH
        opensat = angle_from_x_after_tdc(x01)
        closesat = angle_from_x_after_tdc(x02)
        timing = closesat - opensat # kuinka pitkää auki
        angle_area = 0
        last_area = 0
        for a in np.arange(opensat, closesat, 0.1):
            x = distFromTDC(a)
            traveled_angle = a - opensat
            areaopenfor = timing - traveled_angle
            area = port.areaTheta(a, xp, rt, rb, x01, x02) * constants.milli ** 3
            
            angle_area += (area - last_area)* areaopenfor * 0.1
            last_area = area
            #if a % 5: 
                #print(a) 
                #print(area)
                #print(angle_area)
                
        return angle_area * 6 / rpm
     """       
    
    def compute_effective_areas_array(self, xp, rt, rb, x01, x02):
        areas = []

        for a in np.linspace(0, 360, 3600): # joka 0.1 astetta
            area = self.port_area(distFromTDC(a), xp, rt, rb, x01, x02)
            areas.append(area)


        return np.array(areas) # probs quicker
    
    
        
        
    
class TransferPort(): # ONE TRANSFER PORT YOU GOTTA HAVE MANY TWIN AND MULTIPLY BY TWO IF SYMMETRICAL YOUKNOWADAIMSAINTWIN?
    port: SquarePort = None
    xp = 0
    rt = 0
    rb = 0
    x01 = 0
    x02 = 0
    def __init__(self, xp, rt, rb, x01, x02):
        self.xp = xp
        self.rt = rt
        self.rb = rb
        self.x01 = x01
        self.x02 = x02
        self.port = SquarePort()
        
    def sta(self, rpm):
        return port.sta_abovepiston(self.xp, self.rt, self.rb, self.x01, self.x02, rpm)
    def time_area(self, rpm):
        return port.time_area_abovepiston(self.xp, self.rt, self.rb, self.x01, self.x02, rpm)
    def angle_area(self):
        return port.angle_area_abovepiston(self.xp, self.rt, self.rb, self.x01, self.x02)
        
    
class ExhaustPort():
    port: SquarePort = None
    xp = 0
    rt = 0
    rb = 0
    x01 = 0
    x02 = 0
    def __init__(self, xp, rt, rb, x01, x02):
        self.xp = xp
        self.rt = rt
        self.rb = rb
        self.x01 = x01
        self.x02 = x02
        self.port = SquarePort()
        
    def sta(self, rpm):
        return port.sta_abovepiston(self.xp, self.rt, self.rb, self.x01, self.x02, rpm)
    def time_area(self, rpm):
        return port.time_area_abovepiston(self.xp, self.rt, self.rb, self.x01, self.x02, rpm)
    def angle_area(self):
        return port.angle_area_abovepiston(self.xp, self.rt, self.rb, self.x01, self.x02)
    
    def blowdown_sta(self, transferopensangle: float):
        x02 = distFromTDC(transferopensangle)
        return port.sta_abovepiston(self.xp, self.rt, 0, self.x01, x02) # radius alhaal nolla!!!1
    def blowdown_sta(self, transferport: TransferPort):
        return port.sta_abovepiston(self.xp, self.rt, 0, self.x01, transferport.x01)
        
class IntakePort():
    port: SquarePort = None
    xp = 0
    rt = 0
    rb = 0
    x01 = 0
    x02 = 0
    def __init__(self, xp, rt, rb, x01, x02): # x01 ja x02 on männän etäisyys TDC:stä pitää muuttaa etäisyyksii bdc koska helpompi mittaa näi pitää vaa muistaa et x01 isompi........
        x01angle = angle_from_x_after_bdc(x01)
        x02angle = angle_from_x_after_bdc(x02)
        x01 = distFromBDC(x01angle)
        x02 = distFromBDC(x02angle)
        self.xp = xp
        self.rt = rt
        self.rb = rb
        self.x01 = x01
        self.x02 = x02
        self.port = SquarePort()
        
    def sta(self, rpm):
        return port.sta_belowpiston(self.xp, self.rt, self.rb, self.x01, self.x02, rpm)
    def time_area(self, rpm):
        return port.time_area_belowpiston(self.xp, self.rt, self.rb, self.x01, self.x02, rpm)
    def angle_area(self):
        return port.angle_area_belowpiston(self.xp, self.rt, self.rb, self.x01, self.x02)

        

class Porting:
    intake_port = None
    a_transfer_port = None 
    b_transfer_port = None
    c_transfer_port = None
    exhaust_port = None
    ports = None

    def __init__(self, intake, a, b, c, exh):
        self.intake_port = intake
        self.a_transfer_port = a
        self.b_transfer_port = b
        self.c_transfer_port = c
        self.exhaust_port = exh
        self.ports = [self.intake_port, self.a_transfer_port, self.b_transfer_port, self.c_transfer_port, self.exhaust_port]





# jumal kasikybä plusu pv kone 
stroke = 37.8 # kaikki mm
bore = 50.0
conrod = 80.0
crank_radius = stroke/2
piston_height = 48.0

# imutin sussy wussy
intake_port_heights = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10.2]) # korkeus koordinaatit. Mäppä toisiinsa, esim korkeuskohdassa 1 mm aukko on 10 mm leveä 
intake_port_widths = np.array([10, 9, 8, 7, 6, 6, 4, 4, 4, 4,2]) # mm leveys per millimetri, tän voi interpoloida sitte saadaa massiivisen kivoja tuloksia

#intake_port = Port(intake_port_heights, intake_port_widths, 110)
#updbtn = tk.Button(root, text="upd port widths", command=update_data(cells, intake_port))
#updbtn.pack()
# Plot results


port = SquarePort()
# ntake_port.plot();
fig, ax = plt.subplots()

figport, axport = plt.subplots()
figport.suptitle("imuportti")
angle = np.linspace(0, 360, num=360*10)

# ax.plot(angle, distFromTDC(angle))

ax.plot(angle, distFromBDC(angle))
# time area calculationssss
sta = port.sta_abovepiston(25,2,2,20,distFromTDC(180),9000)
print(sta)
# yippeeeeeeeeeeeeeeeeeweeeeeeeeeeeeeeeeeeeeeeeeeeeweedeeeedeeeeeedeeeee

sta2 = port.sta_belowpiston(5,2,2,10,distFromTDC(180),9000)
print(sta2)
port.plot(axport, port.getWidths(25,2,2,20,distFromTDC(180)), 20, distFromTDC(180))
port.plot(axport, port.getWidths(5,2,2,30,distFromTDC(180)), 30, distFromTDC(180))
#print(port.time_area_goofyway(25, 2, 2, 20, distFromTDC(180), 9000) / swept_volume())
effectiveareas = port.compute_effective_areas_array(25, 2, 2, 25, distFromTDC(180))
ax.plot(angle, effectiveareas)
td = np.linspace(0, stroke + 10)

vw = np.vectorize(lambda t: port.port_width(t, 25, 2, 2, 15, distFromTDC(180)))
ax.plot(td, vw(td))

print(swept_volume())
# RICH LIKE A WHITE BITCH I SHOULD GO BLOND BITCH 🗣️🗣️🗣️🗣️
# joo kuka vitun retardi nää o kirjottanu o my days 
plt.show()
root.mainloop()