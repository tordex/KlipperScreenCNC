import gi
import logging

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel

from ks_includes.widgets.keypad import Keypad
from ks_includes.KlippyGcodes import KlippyGcodes

AXIS_X = "X"
AXIS_Y = "Y"
AXIS_Z = "Z"

def create_panel(*args):
    return MainPanel(*args)

class MainPanel(ScreenPanel):
    distance = 1
    distances = ['.1', '.5', '1', '5', '10', '25', '50']

    def __init__(self, screen, title, back=False):
        super().__init__(screen, title, False)

    def initialize(self, panel_name, items, extrudercount):
        _ = self.lang.gettext
        print("### Making MainMenu")

        # Define Axis text labels
        axis_grid = self._gtk.HomogeneousGrid()
        axis_grid.set_direction(Gtk.TextDirection.LTR)

        self.labels['pos_x'] = Gtk.Label("X: 0")
        self.labels['pos_x'].get_style_context().add_class("position")

        self.labels['pos_y'] = Gtk.Label("Y: 0", "position")
        self.labels['pos_y'].get_style_context().add_class("position")
        
        self.labels['pos_z'] = Gtk.Label("Z: 0", "position")
        self.labels['pos_z'].get_style_context().add_class("position")

        axis_grid.attach(self.labels['pos_x'], 0, 0, 1, 1)
        axis_grid.attach(self.labels['pos_y'], 1, 0, 1, 1)
        axis_grid.attach(self.labels['pos_z'], 2, 0, 1, 1)
        
        self.labels['move_dist'] = Gtk.Label(_("Move Distance (mm)"))

        # Define Move Axis buttons
        move_buttons_grid = self._gtk.HomogeneousGrid()

        self.labels['x+'] = self._gtk.ButtonImage("arrow-right", _("X+"), "color1")
        self.labels['x+'].connect("clicked", self.move, AXIS_X, "+")
        self.labels['x-'] = self._gtk.ButtonImage("arrow-left", _("X-"), "color1")
        self.labels['x-'].connect("clicked", self.move, AXIS_X, "-")

        self.labels['y+'] = self._gtk.ButtonImage("arrow-up", _("Y+"), "color2")
        self.labels['y+'].connect("clicked", self.move, AXIS_Y, "+")
        self.labels['y-'] = self._gtk.ButtonImage("arrow-down", _("Y-"), "color2")
        self.labels['y-'].connect("clicked", self.move, AXIS_Y, "-")

        self.labels['z+'] = self._gtk.ButtonImage("z-farther", _("Z+"), "color3")
        self.labels['z+'].connect("clicked", self.move, AXIS_Z, "+")
        self.labels['z-'] = self._gtk.ButtonImage("z-closer", _("Z-"), "color3")
        self.labels['z-'].connect("clicked", self.move, AXIS_Z, "-")

        move_buttons_grid.attach(self.labels['x+'], 2, 1, 1, 1)
        move_buttons_grid.attach(self.labels['x-'], 0, 1, 1, 1)
        move_buttons_grid.attach(self.labels['y+'], 1, 0, 1, 1)
        move_buttons_grid.attach(self.labels['y-'], 1, 1, 1, 1)
        move_buttons_grid.attach(self.labels['z+'], 0, 0, 1, 1)
        move_buttons_grid.attach(self.labels['z-'], 2, 0, 1, 1)

        # Define quick actions buttons
        actions_grid = Gtk.Grid()

        self.labels['home'] = self._gtk.Button(_("Home All"), "action")
        self.labels['home'].connect("clicked", self.home)

        self.labels['zero-xy'] = self._gtk.Button(_("XY=0"), "action")
        script = {"script": "G92 X0 Y0"}
        self.labels['zero-xy'].connect("clicked", self._screen._confirm_send_action,
                                          _("Are you sure you wish zero X and Y axis?"),
                                          "printer.gcode.script", script)

        self.labels['zero-z'] = self._gtk.Button(_("Z=0"), "action")
        script = {"script": "G92 Z0"}
        self.labels['zero-z'].connect("clicked", self._screen._confirm_send_action,
                                          _("Are you sure you wish zero Z axis?"),
                                          "printer.gcode.script", script)

        self.labels['zero-all'] = self._gtk.Button(_("XYZ=0"), "action")
        script = {"script": "G92 X0 Y0 Z0"}
        self.labels['zero-all'].connect("clicked", self._screen._confirm_send_action,
                                          _("Are you sure you wish zero X, Y and Z axis?"),
                                          "printer.gcode.script", script)
        
        self.labels['probe_off'] = self._gtk.Button(_("Probe"), "action")
        script = {"script": "POBE_ZERO_OFF"}
        self.labels['probe_off'].connect("clicked", self._screen._confirm_send_action,
                                          _("Are you sure you wish probe Z height with offset?"),
                                          "printer.gcode.script", script)
        
        self.labels['probe'] = self._gtk.Button(_("Probe OFF=0"), "action")
        script = {"script": "POBE_ZERO"}
        self.labels['probe'].connect("clicked", self._screen._confirm_send_action,
                                          _("Are you sure you wish probe Z height with offset==0?"),
                                          "printer.gcode.script", script)
        
        actions_grid.attach(self.labels['home'], 0, 0, 1, 1)
        actions_grid.attach(self.labels['zero-xy'], 0, 1, 1, 1)
        actions_grid.attach(self.labels['zero-z'], 0, 2, 1, 1)
        actions_grid.attach(self.labels['zero-all'], 0, 3, 1, 1)
        actions_grid.attach(self.labels['probe_off'], 0, 4, 1, 1)
        actions_grid.attach(self.labels['probe'], 0, 5, 1, 1)

        # Defind move distance
        distgrid = Gtk.Grid()
        j = 0
        for i in self.distances:
            self.labels[i] = self._gtk.ToggleButton(i)
            self.labels[i].set_direction(Gtk.TextDirection.LTR)
            self.labels[i].connect("clicked", self.change_distance, i)
            ctx = self.labels[i].get_style_context()
            if (self._screen.lang_ltr and j == 0) or (not self._screen.lang_ltr and j == len(self.distances)-1):
                ctx.add_class("distbutton_top")
            elif (not self._screen.lang_ltr and j == 0) or (self._screen.lang_ltr and j == len(self.distances)-1):
                ctx.add_class("distbutton_bottom")
            else:
                ctx.add_class("distbutton")
            if i == "1":
                ctx.add_class("distbutton_active")
            distgrid.attach(self.labels[i], j, 0, 1, 1)
            j += 1

        self.labels["1"].set_active(True)

        # Define other buttons
        other_buttons_grid = Gtk.Grid()

        self.labels['toolchanger'] = self._gtk.ButtonImage("toolchanger", _("Tool Change"), "color1")
        self.labels['toolchanger'].connect("clicked", self.menu_item_clicked, "tool_changer", {"panel": "tool_changer", "name": "tool_changer"})

        self.labels['config'] = self._gtk.ButtonImage("settings", _("Configuration"), "color2")
        self.labels['config'].connect("clicked", self._screen._go_to_submenu, "config")

        self.labels['print'] = self._gtk.ButtonImage("print", _("Start"), "color4")
        self.labels['print'].connect("clicked", self.menu_item_clicked, "print", {"panel": "print", "name": "print"})

        other_buttons_grid.attach(self.labels['config'], 0, 0, 1, 1)
        other_buttons_grid.attach(self.labels['toolchanger'], 0, 1, 1, 1)
        other_buttons_grid.attach(self.labels['print'], 0, 2, 1, 1)

        # Pack move buttons with action buttons
        move_grid = Gtk.Grid()
        move_grid.attach(axis_grid, 0, 0, 2, 1)
        move_grid.attach(move_buttons_grid, 0, 1, 1, 1)
        move_grid.attach(actions_grid, 1, 1, 1, 1)
        move_grid.attach(self.labels['move_dist'], 0, 2, 2, 1)
        move_grid.attach(distgrid, 0, 3, 2, 1)
        move_grid.attach(other_buttons_grid, 3, 0, 1, 4)

        self.content.add(move_grid)
        self.layout.show_all()

    def hide_numpad(self, widget):
        self.devices[self.active_heater]['name'].get_style_context().remove_class("active_device")
        self.active_heater = None

        if self._screen.vertical_mode:
            self.grid.remove_row(1)
            self.grid.attach(self.labels['menu'], 0, 1, 1, 1)
        else:
            self.grid.remove_column(1)
            self.grid.attach(self.labels['menu'], 1, 0, 1, 1)
        self.grid.show_all()

    def process_update(self, action, data):
        if action != "notify_status_update":
            return

        if action == "notify_gcode_response":
            logging.info("data: {}".format(data))

        homed_axes = self._screen.printer.get_stat("toolhead", "homed_axes")
        if homed_axes == "xyz":
            if "gcode_move" in data and "gcode_position" in data["gcode_move"]:
                self.labels['pos_x'].set_text("X: %.2f" % (data["gcode_move"]["gcode_position"][0]))
                self.labels['pos_y'].set_text("Y: %.2f" % (data["gcode_move"]["gcode_position"][1]))
                self.labels['pos_z'].set_text("Z: %.2f" % (data["gcode_move"]["gcode_position"][2]))
        else:
            if "x" in homed_axes:
                if "gcode_move" in data and "gcode_position" in data["gcode_move"]:
                    self.labels['pos_x'].set_text("X: %.2f" % (data["gcode_move"]["gcode_position"][0]))
            else:
                self.labels['pos_x'].set_text("X: ?")
            if "y" in homed_axes:
                if "gcode_move" in data and "gcode_position" in data["gcode_move"]:
                    self.labels['pos_y'].set_text("Y: %.2f" % (data["gcode_move"]["gcode_position"][1]))
            else:
                self.labels['pos_y'].set_text("Y: ?")
            if "z" in homed_axes:
                if "gcode_move" in data and "gcode_position" in data["gcode_move"]:
                    self.labels['pos_z'].set_text("Z: %.2f" % (data["gcode_move"]["gcode_position"][2]))
            else:
                self.labels['pos_z'].set_text("Z: ?")
        return

    def show_numpad(self, widget):
        _ = self.lang.gettext

        if self.active_heater is not None:
            self.devices[self.active_heater]['name'].get_style_context().remove_class("active_device")
        self.active_heater = self.popover_device
        self.devices[self.active_heater]['name'].get_style_context().add_class("active_device")

        if "keypad" not in self.labels:
            self.labels["keypad"] = Keypad(self._screen, self.change_target_temp, self.hide_numpad)
        self.labels["keypad"].clear()

        if self._screen.vertical_mode:
            self.grid.remove_row(1)
            self.grid.attach(self.labels["keypad"], 0, 1, 1, 1)
        else:
            self.grid.remove_column(1)
            self.grid.attach(self.labels["keypad"], 1, 0, 1, 1)
        self.grid.show_all()

        self.labels['popover'].popdown()

    def change_distance(self, widget, distance):
        if self.distance == distance:
            return
        logging.info("### Distance " + str(distance))

        ctx = self.labels[str(self.distance)].get_style_context()
        ctx.remove_class("distbutton_active")

        self.distance = distance
        ctx = self.labels[self.distance].get_style_context()
        ctx.add_class("distbutton_active")
        for i in self.distances:
            if i == self.distance:
                continue
            self.labels[str(i)].set_active(False)

    def move(self, widget, axis, dir):
        if self._config.get_config()['main'].getboolean("invert_%s" % axis.lower(), False):
            dir = "-" if dir == "+" else "+"

        dist = str(self.distance) if dir == "+" else "-" + str(self.distance)
        config_key = "move_speed_z" if axis == AXIS_Z else "move_speed_xy"

        speed = None
        printer_cfg = self._config.get_printer_config(self._screen.connected_printer)

        if printer_cfg is not None:
            speed = printer_cfg.getint(config_key, None)

        if speed is None:
            speed = self._config.get_config()['main'].getint(config_key, 20)

        speed = max(1, speed)

        self._screen._ws.klippy.gcode_script(
            "%s\n%s %s%s F%s%s" % (
                KlippyGcodes.MOVE_RELATIVE, KlippyGcodes.MOVE, axis, dist, speed*60,
                "\nG90" if self._printer.get_stat("gcode_move", "absolute_coordinates") is True else ""
            )
        )
