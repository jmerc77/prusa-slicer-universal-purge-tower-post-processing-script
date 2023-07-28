#settings...

#position:
purge_x=15
purge_y=15
#rectangle size (from position to position + size):
purge_w=10
purge_l=10
#line_width:
purge_width=1
#speed:
purge_spd=30
#minimum layer height of purge:
min_lh=0.1

color_change="M600"

#No touch below! (unless you know what you are doing)
import sys
import re
import os
import math

#auto configed
ret_spd=None
ret_l=None
fil_d=None
flow=None
nd=None
t_spd=None
lh=0

def calc_e(l,lh,ew,flow,fil_d):
    return (lh*flow*ew*l)/(math.pi/4*(fil_d**2))

if __name__=="__main__":
    file_in=sys.argv[1]
    with open(file_in, "r") as f:
        lines = f.readlines()
        f.close()

    
    for i in range(len(lines)-1,0,-1):
        if "; retract_speed = " in lines[i]:
            ret_spd=float(lines[i].replace("; retract_speed = ","").replace("\n",""))
        if "; retract_length = " in lines[i]:
            ret_l=float(lines[i].replace("; retract_length = ","").replace("\n",""))
        if "; filament_diameter = " in lines[i]:
            fil_d=float(lines[i].replace("; filament_diameter = ","").replace("\n",""))
        if "; extrusion_multiplier = " in lines[i]:
            flow=float(lines[i].replace("; extrusion_multiplier = ","").replace("\n",""))
        if "; nozzle_diameter = " in lines[i]:
            nd=float(lines[i].replace("; nozzle_diameter = ","").replace("\n",""))
        if "; travel_speed = " in lines[i]:
            t_spd=float(lines[i].replace("; travel_speed = ","").replace("\n",""))
            
        if ret_spd != None and ret_l != None and fil_d != None and flow != None and nd != None and t_spd != None:
            break
    with open(file_in, "w",newline="") as fo:
        lh1=0
        z=0
        last_move=""
        ret_move=""
        last_width=""
        purge=False
        e=0
        last_e=0
        for i in range(len(lines)):
            if ("G1" in lines[i] or "G0" in lines[i]) and ("X" in lines[i] or "Y" in lines[i]):
                last_move=lines[i]
                if "E" in last_move:
                    last_e=last_move[last_move.index("E"):]
                    ret_move=last_move[0:last_move.index("E")-1]+"\n"
            if ";Z:" in lines[i]:
                temp=float(lines[i].replace(";Z:","").replace("\n",""))
                lh=round(temp-z,2)
                if lh>=min_lh and round(temp,2)>z:
                    z=round(temp,2)
                    purge=True
            if ";WIDTH:" in lines[i]:
                last_width=lines[i]
            #force color change over purge square
            if lines[i].strip(" \n\r\t").startswith(color_change):
                #retract
                fo.write("G10\n")
                #travel to square
                fo.write("G1 X"+str(purge_x)+" Y"+str(purge_y)+" F"+str(60*t_spd)+"\n")
                #unretract
                fo.write("G11\n")
                #M600 will auto fill at bottom
            if "; printing object" in lines[i] and purge==True:
                #detect extra retraction
                ex_ret=-1
                ex_g92=False
                for j in range(i,i+10):
                    if ("G1" in lines[j] or "G0" in lines[j]) and "E" in lines[j] and ex_ret<0:
                        if "F" in lines[j]:
                            if round(float(lines[j][lines[j].index("E")+1:lines[j].index(" ",lines[j].index("E"))]),2) < round(float(last_e[1:-1]),2):
                                ex_ret=j
                                lines[j]=";"+lines[j]
                        else:
                            if round(float(lines[j][lines[j].index("E")+1:-1]),2) < round(float(last_e[1:-1]),2):
                                ex_ret=j
                                lines[j]=";"+lines[j]
                    if "G92 E" in lines[j]:
                        ex_g92=True
                #for corrected preview
                fo.write("; printing object purge id:-1 copy 0\n")
                fo.write(";TYPE:Skirt/Brim\n")
                fo.write(";WIDTH:"+str(purge_width)+"\n")
                
                #retract & move
                fo.write("G1 E"+str(float(last_e[1:-1])-ret_l)+" F"+str(60*ret_spd)+"\n")
                fo.write("G92 E0\n")
                fo.write("G1 X"+str(purge_x)+" Y"+str(purge_y)+" F"+str(60*t_spd)+"\n")
                fo.write("G1 Eret_l F"+str(60*ret_spd)+"\n")
                #print a hollow square
                e=calc_e(purge_w,lh,purge_width,flow,fil_d)+ret_l
                fo.write("G1 X"+str(purge_x+purge_w)+" Y"+str(purge_y)+" E"+str(e)+" F"+str(60*purge_spd)+"\n")
                e+=calc_e(purge_l,lh,purge_width,flow,fil_d)
                fo.write("G1 X"+str(purge_x+purge_w)+" Y"+str(purge_y+purge_l)+" E"+str(e)+" F"+str(60*purge_spd)+"\n")
                e+=calc_e(purge_w,lh,purge_width,flow,fil_d)
                fo.write("G1 X"+str(purge_x)+" Y"+str(purge_y+purge_l)+" E"+str(e)+" F"+str(60*purge_spd)+"\n")
                e+=calc_e(purge_l,lh,purge_width,flow,fil_d)
                fo.write("G1 X"+str(purge_x)+" Y"+str(purge_y)+" E"+str(e)+" F"+str(60*purge_spd)+"\n")
                #retract & return
                fo.write("G1 E"+str(e-ret_l)+" F"+str(60*ret_spd)+"\n")#retract
                if ex_ret<0:
                    fo.write(ret_move[:-1]+" F"+str(60*t_spd)+"\n") #return
                    fo.write("G1 E"+str(e)+" F"+str(60*ret_spd)+"\n")#unretract
                    if not ex_g92:
                        fo.write("G92 "+last_e)
                #for corrected preview
                fo.write("; stop printing object purge id:-1 copy 0\n")
                fo.write(";LAYER_CHANGE\n")
                fo.write(";Z:"+str(z)+"\n")
                fo.write(";HEIGHT:"+str(lh1)+"\n")
                fo.write(last_width)
                purge=False
            #for corrected preview
            if ";HEIGHT:" in lines[i] and purge==True:
                lh1=float(lines[i].replace(";HEIGHT:","").replace("\n",""))
                fo.write(";HEIGHT:"+str(lh)+"\n")
            else:
                fo.write(lines[i])
        fo.close()
