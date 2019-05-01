#!/usr/bin/python
# coding: utf-8

import sys

try:
    if sys.version_info[0] < 3: #switch between python 2 and 3 because package name changed
        import Tkinter as tk
    else:
        import tkinter as tk
except ImportError :
    print("Error trying to import tkinter. Use 'sudo apt-get install python-tk' on Unix for python 2, or 'sudo apt-get install python3-tk' for python 3".encode("utf8"))
    sys.exit(0)

from collections import defaultdict
import yaml

#I'm sorry there are so many globals :( 
grid = {} # (coordinate_tuple) -> Button map
layout_dims = (0, 0) # size of the map
out_entry = None

bg_base_color = "grey"
active_bg_base_color = "lightgray"
pointer_carried_color = "grey"
ep_color = "orange"
ds_color = "black"
es_color = "yellow"
pb_color = "green"
pb_position = (-1, -1) # position of the previous player_base, for unicity handling

b_enemy_path = None
b_defense_spawn = None
b_player_base = None
b_enemy_spawn = None


def loadLayout(event): # event is just here to accomodate key binding
    layout_file_path = layout_load_entry.get()
    layout = {} 
    loaded_map = {} # coor_tuple -> color map
    with open("{}".format(layout_file_path).encode("utf8")) as layout_yaml:
        layout = yaml.load(layout_yaml)
    
    layout_dims = tuple(layout["Layout_dims"])

    for entry_name in ["Enemy_path", "Player_base", "Enemy_spawn", "Defense_spawn"]:
        coor_lst = layout[entry_name]
        for coor in coor_lst:
            if entry_name == "Enemy_path":
                loaded_map[tuple(coor)] = ep_color
            elif entry_name == "Player_base":
                loaded_map[tuple(coor)] = pb_color
            elif entry_name == "Enemy_spawn":
                loaded_map[tuple(coor)] = es_color
            elif entry_name == "Defense_spawn":
                loaded_map[tuple(coor)] = ds_color

    generateLayout(event, loaded_map)
        

def buildExistingLayout(loaded_map):
    grid_frame = tk.Frame(label_grid_frame, borderwidth=2, relief="flat")
    grid_frame.grid(row=0, column=0, sticky="W")
    
    for row in range(3, layout_dims[0]+3):
        for column in range(layout_dims[1]):
            b_color = loaded_map.get((row, column), bg_base_color)
            b = tk.Button(grid_frame, relief="flat", background=b_color, activebackground=active_bg_base_color, borderwidth=1, command=lambda r=row, c=column: click((r, c)))
            b.grid(row=row, column=column) # ajouter sticky=N+S+E+W pr le resize
            grid[(row, column)] = b


def buildNewLayout():
    grid_frame = tk.Frame(label_grid_frame, borderwidth=2, relief="flat")
    grid_frame.grid(row=0, column=0, sticky="W")
    
    for row in range(3, layout_dims[0]+3):
        for column in range(layout_dims[1]):
            b = tk.Button(grid_frame, relief="flat", background=bg_base_color, activebackground=active_bg_base_color, borderwidth=1, command=lambda r=row, c=column: click((r, c)))
            b.grid(row=row, column=column) # ajouter sticky=N+S+E+W pr le resize
            grid[(row, column)] = b


def generateLayout(event=None, loaded_map={}): # event is just here to accomodate key binding
    global grid
    global layout_dims
    global out_entry
    global b_enemy_path
    global b_defense_spawn
    global b_player_base
    global b_enemy_spawn
    
    layout_dims = (int(row_entry.get()), int(col_entry.get()))
    
    # Grid manager views the window as a matrix where one specifies the coordinates of an object based on the row/column indices
    # It is a simple, precise manager
    # Plus, since the core of this interface is a grid of button, and considering you can't mix the managers, gris is the weapon of choice
    
    # In the case we are refreshing the layout (and not generating it for the first time)
    if label_grid_frame.winfo_children():
        for child in label_grid_frame.winfo_children():
            child.destroy()
    
    # Build the layout
    if loaded_map:
        buildExistingLayout(loaded_map)
    else:
        buildNewLayout()
    
    
    # Build the switches that will allow the user to specify which type of in-game element he wants to place
    label_switch_frame = tk.LabelFrame(command_frame, text="Element type", relief="groove")
    label_switch_frame.grid(row=0, column=1, sticky="W")
    
    switch_frame = tk.Frame(label_switch_frame, borderwidth=2, relief="flat")
    switch_frame.grid(row=0, column=0)
    
    b_enemy_path = tk.Button(switch_frame, text="Enemy path", relief="raised", command=lambda: setAction("ep"))
    b_enemy_path.grid(row=0, column=0, sticky="W")
    b_defense_spawn = tk.Button(switch_frame, text="Defense spawn", relief="raised", command=lambda: setAction("ds"))
    b_defense_spawn.grid(row=1, column=0, sticky="W")
    b_player_base = tk.Button(switch_frame, text="Player Base", relief="raised", command=lambda: setAction("pb"))
    b_player_base.grid(row=2, column=0, sticky="W")
    b_enemy_spawn = tk.Button(switch_frame, text="Enemy spawn", relief="raised", command=lambda: setAction("es"))
    b_enemy_spawn.grid(row=3, column=0, sticky="W")
    
    dumb_label = tk.Label(switch_frame, text="", relief="flat") #useless label, to make a separation between the other buttons and the reset button
    dumb_label.grid(row=4, column=0, sticky="W")
    b_reset_layout = tk.Button(switch_frame, text="Reset layout", relief="raised", command=lambda: resetLayout())
    b_reset_layout.grid(row=5, column=0, sticky="W")
    
    # Build the output info
    # Pour le chemin d'output je sais pas trop quoi faire, donc j'ai fait le minimum : output à l'endroit où le script est executé
    out_frame = tk.Frame(main_frame, borderwidth=2, relief="flat")
    out_frame.grid(row=3, column=0)
    
    out_label = tk.Label(out_frame, text="Output path to map file : ", relief="flat")
    out_label.grid(row=0, column=0, sticky="W")
    
    out_input = tk.StringVar()
    out_input.set("map_{}x{}.yml".format(layout_dims[0], layout_dims[1]))
    
    out_entry = tk.Entry(out_frame, textvariable=out_input, width=30) #bind the fields to an entry so we can retrieve and manipulate the values
    out_entry.grid(row=0, column=1, sticky="W")
    
    b_generate = tk.Button(out_frame, text="Generate map", relief="raised", command=lambda: generateMap())
    b_generate.grid(row=1, column=1, sticky="E")
    

def click(coor_tuple):
    # When clicking on any button of the grid
    global bg_base_color
    global pointer_carried_color
    global pb_position
    
    if grid[coor_tuple]["bg"] == pointer_carried_color: # if clicking twice on a button : reverse to base color 
        grid[coor_tuple]["bg"] = bg_base_color
    
    elif pointer_carried_color == pb_color and pb_position == (-1, -1): # first time positioning player base
        pb_position = coor_tuple
        grid[coor_tuple]["bg"] = pointer_carried_color
    
    elif pointer_carried_color == pb_color and pb_position != (-1, -1): # repositioning player base, reinit former position, so there is always only one player base
        grid[pb_position]["bg"] = bg_base_color
        pb_position = coor_tuple
        grid[coor_tuple]["bg"] = pointer_carried_color
    
    else:
        grid[coor_tuple]["bg"] = pointer_carried_color


def setAction(action_string):
    # Selecting the type of in-game element you want to place on the layout
    global pointer_carried_color
    global ep_color
    global ds_color
    global pb_color
    global es_color
    global b_enemy_path
    global b_defense_spawn
    global b_player_base
    global b_enemy_spawn
    
    # This switch uses the color (aka game element) memorized to reinitialize its associated button's state
    if pointer_carried_color == ep_color: # setting enemy path
        b_enemy_path.config(relief="raised", state="active")
    elif pointer_carried_color == ds_color: # setting defense spawn spot
        b_defense_spawn.config(relief="raised", state="active")
    elif pointer_carried_color == pb_color: # setting player base
        b_player_base.config(relief="raised", state="active")
    elif pointer_carried_color == es_color: # setting enemy spawn
        b_enemy_spawn.config(relief="raised", state="active")
    
    # This switch presses the button (eg game element) chosen by the user
    if action_string == "ep": # setting enemy path
        pointer_carried_color = ep_color
        b_enemy_path.config(relief="sunken", state="disabled")
    elif action_string == "ds": # setting defense spawn spot
        pointer_carried_color = ds_color
        b_defense_spawn.config(relief="sunken", state="disabled")
    elif action_string == "pb": # setting player base
        pointer_carried_color = pb_color
        b_player_base.config(relief="sunken", state="disabled")
    elif action_string == "es": # setting enemy spawn
        pointer_carried_color = es_color
        b_enemy_spawn.config(relief="sunken", state="disabled")


def resetLayout():
    # Reverts all cells grey
    for coor_tuple, button in grid.iteritems():
        if button["bg"] != bg_base_color:
            button["bg"] = bg_base_color


def reorderEnemyPath(start_tuple, unordered_enemy_path):
    # Given a list of tuples, reoders them by neighboring values from a starting tuple
    # returns the reodered list
    # used to build the enemy path as a list from the coordinate of the base to the edge of the map
    
    #TODO si au test des direction je fail, je dois péter adjacence
    print("unordered : {}".format(unordered_enemy_path).encode("utf8"))
    print("starting from : {}\n".format(start_tuple).encode("utf8"))
    reordered_enemy_path = []
    enemy_path_set = {tuple(coor_lst) for coor_lst in unordered_enemy_path} # arrives as a list of lists, casted into a set of tuple (note : lists are unashable)
    
    current_tuple = start_tuple
    for i in range(0, len(unordered_enemy_path)): # there are len(unordered_enemy_path) coordiantes to reorder
        #Generate all 4 possible directions from the current position, then check which is in our coordinate set
        candidate_tuple_up = (current_tuple[0]+1, current_tuple[1])
        candidate_tuple_down = (current_tuple[0]-1, current_tuple[1])
        candidate_tuple_right = (current_tuple[0], current_tuple[1]+1)
        candidate_tuple_left = (current_tuple[0], current_tuple[1]-1)
        
        for candidate_tuple in [candidate_tuple_up, candidate_tuple_down, candidate_tuple_right, candidate_tuple_left]: #TODO la liste est un biais, si on veut autoriser les loops, ac des inter/union taille 1 ?
            if candidate_tuple in enemy_path_set:
                reordered_enemy_path.append(list(candidate_tuple))
                enemy_path_set.remove(candidate_tuple) # not removing allows loops in the path
                current_tuple = candidate_tuple
                break # only one neighbor is added at a time
    print("reordered : {}".format(reordered_enemy_path).encode("utf8"))
    return reordered_enemy_path


def generateMap():
    # Outputs a mapping with 1 entry per unit_type -> [[x_coor, y_coor], [...], ... ]
    # + 1 entry "Layout_dims" with 2-elements list containing the size of the layout 
    out_path = out_entry.get()
    yaml_map = {}
    yaml_map["Layout_dims"] = [layout_dims[0], layout_dims[1]] 
    
    for coor_tuple, button in grid.iteritems():
        color = button["bg"]
        if color == ep_color:
            yaml_map["Enemy_path"] = yaml_map.get("Enemy_path", [])
            yaml_map["Enemy_path"].append(list(coor_tuple))
        elif color == ds_color:
            yaml_map["Defense_spawn"] = yaml_map.get("Defense_spawn", [])
            yaml_map["Defense_spawn"].append(list(coor_tuple))
        elif color == pb_color:
            yaml_map["Player_base"] = yaml_map.get("Player_base", [])
            yaml_map["Player_base"].append(list(coor_tuple))
        elif color == es_color:
            yaml_map["Enemy_spawn"] = yaml_map.get("Enemy_spawn", [])
            yaml_map["Enemy_spawn"].append(list(coor_tuple))

    #TODO  : si y'a pas de spawn, il faut péter
    enemy_path_reordered = reorderEnemyPath(yaml_map["Enemy_spawn"][0], yaml_map["Enemy_path"])
    yaml_map["Enemy_path"] = enemy_path_reordered
    
    with open("{}".format(out_path).encode("utf8"), 'w') as out_yml:
        yaml.dump(yaml_map, out_yml, default_flow_style=False)
    

# Initialize the interface
window = tk.Tk() # root element
window.title("The Fabulous Map Editor")

# Intermediate frame, holding every widget to generate layouts (Initial look)
start_frame = tk.Frame(window, borderwidth=2, relief="flat")
# important : always call the manager (here grid, possibly place or pack) ON A SEPARATE LINE, otherwise we can't assign the object (manager returns None) 
start_frame.grid(row=0, column=0, sticky="W") # sticky makes the widget stick to the left (West) side of its parent

# Build a new layout from scratch
label_new_layout_frame = tk.LabelFrame(start_frame, text="New layout", relief="groove")
label_new_layout_frame.grid(row=0, column=0, sticky="W")

row_label = tk.Label(label_new_layout_frame, text="number of rows in layout : ", relief="flat")
row_label.grid(row=0, column=0, sticky="W")
col_label = tk.Label(label_new_layout_frame, text="number of columns in layout : ", relief="flat")
col_label.grid(row=1, column=0, sticky="W")

row_input = tk.StringVar()
col_input = tk.StringVar()

row_entry = tk.Entry(label_new_layout_frame, textvariable=row_input, width=10) #bind the fields to an entry so we can retrieve and manipulate the values
row_entry.grid(row=0, column=1, sticky="W")
row_entry.focus_set() # give focus to this entry

col_entry = tk.Entry(label_new_layout_frame, textvariable=col_input, width=10)
col_entry.grid(row=1, column=1, sticky="W")

b_generate_layout = tk.Button(label_new_layout_frame, text="Generate layout", relief="raised", command=lambda: generateLayout)
b_generate_layout.grid(row=1, column=2, sticky="W")
b_generate_layout.bind("<Button-1>", generateLayout) # bind to the left mouse button click
b_generate_layout.bind("<Return>", generateLayout) # bind to the Enter key
b_generate_layout.bind("<KP_Enter>", generateLayout) # bind to the Enter key of the numeric pad. Full list at http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/key-names.html

# Separator between frames
dummy_label = tk.Label(start_frame, relief="flat")
dummy_label.grid(row=1, column=0, sticky="W")

# Load new layout
label_load_layout_frame = tk.LabelFrame(start_frame, text="Load existing layout file", relief="groove")
label_load_layout_frame.grid(row=2, column=0, sticky="W")

layout_load_label = tk.Label(label_load_layout_frame, text="Load file : ", relief="flat")
layout_load_label.grid(row=0, column=0, sticky="W")

layout_load_input = tk.StringVar()

layout_load_entry = tk.Entry(label_load_layout_frame, textvariable=layout_load_input, width=30) #bind the fields to an entry so we can retrieve and manipulate the values
layout_load_entry.grid(row=0, column=1, sticky="W")

b_load_existing_layout = tk.Button(label_load_layout_frame, text="Load", relief="raised", command=lambda: loadLayout)
b_load_existing_layout.grid(row=0, column=2, sticky="W")
b_load_existing_layout.bind("<Button-1>", loadLayout) # bind to the left mouse button click
b_load_existing_layout.bind("<Return>", loadLayout) # bind to the Enter key
b_load_existing_layout.bind("<KP_Enter>", loadLayout) # bind to the Enter key of the numeric pad.

main_frame = tk.Frame(window, borderwidth=2) # intermediate frame, holding every widget generated by generateLayout
main_frame.grid(row=2, column=0, columnspan=2, sticky="W")

# Yet another intermediate frame, so the layout and the buttons stay together
command_frame = tk.Frame(main_frame, borderwidth=2, relief="flat")
command_frame.grid(row=0, column=0, sticky="W")

# Frame holding the grid, to ease refresh
label_grid_frame = tk.LabelFrame(command_frame, text="Map layout")
label_grid_frame.grid(row=0, column=0, sticky="W")

'''
grid_frame = tk.Frame(command_frame, borderwidth=2, relief="flat")
grid_frame.grid(row=0, column=0, sticky="W")
'''
# TODO il faudrait checker que les enemy paths se font selons des cases adjacentes

window.mainloop()


