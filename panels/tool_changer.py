import gi
import logging
import re

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel

from ks_includes.widgets.keypad import Keypad
from ks_includes.KlippyGcodes import KlippyGcodes

AXIS_X = "X"
AXIS_Y = "Y"
AXIS_Z = "Z"

def create_panel(*args):
    return ToolChangerPanel(*args)

class ToolChangerPanel(ScreenPanel):
    distance = 1
    distances = ['.1', '.5', '1', '5', '10', '25', '50']

    def __init__(self, screen, title, back=False):
        super().__init__(screen, title, back)

    def activate(self):
        self.first_tool = None
        self.labels["tip"].set_text("Step 1: Probe the first tool height with the Probe button")
        self.labels["probe1"].set_text("TOOL #1: ?")
        self.labels["probe2"].set_text("TOOL #2: ?")
        self._screen._ws.klippy.gcode_script("GET_POSITION")

    def initialize(self, panel_name):
        _ = self.lang.gettext

        self.first_tool = None

        self.labels['pos_z'] = Gtk.Label("Z: 0")
        self.labels['pos_z'].get_style_context().add_class("position")
        self.labels['pos_z'].set_halign(Gtk.Align.START)

        self.labels['probe1'] = Gtk.Label("TOOL #1: ?")
        self.labels['probe1'].get_style_context().add_class("position")
        self.labels['probe1'].set_halign(Gtk.Align.START)

        self.labels['probe2'] = Gtk.Label("TOOL #2: ?")
        self.labels['probe2'].get_style_context().add_class("position")
        self.labels['probe2'].set_halign(Gtk.Align.START)

        self.labels['tip'] = Gtk.Label("Step 1: Probe the first tool height with the Probe button")
        self.labels['tip'].get_style_context().add_class("position")
        self.labels['tip'].set_line_wrap(True)
        self.labels['tip'].set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

        self.labels['z+'] = self._gtk.ButtonImage("z-farther", _("Z+"), "color1")
        self.labels['z+'].connect("clicked", self.move, AXIS_Z, "+")
        self.labels['z-'] = self._gtk.ButtonImage("z-closer", _("Z-"), "color2")
        self.labels['z-'].connect("clicked", self.move, AXIS_Z, "-")

        self.labels['probe'] = self._gtk.ButtonImage("arrow-down", _("Probe"), "color3")
        self.labels['probe'].connect("clicked", self._screen._send_action, "printer.gcode.script", {"script": "PROBE"})

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

        labels_box = Gtk.VBox(spacing=0)
        labels_box.set_hexpand(True)
        labels_box.set_vexpand(False)
        labels_box.set_halign(Gtk.Align.START)
        labels_box.add(self.labels['pos_z'])
        labels_box.add(self.labels['probe1'])
        labels_box.add(self.labels['probe2'])

        buttons_box = Gtk.HBox(spacing=0)
        buttons_box.set_hexpand(True)
        buttons_box.set_vexpand(False)
        buttons_box.add(self.labels['z+'])
        buttons_box.add(self.labels['z-'])
        buttons_box.add(self.labels['probe'])

        final_box = Gtk.VBox(spacing=0)
        final_box.set_hexpand(True)
        final_box.set_vexpand(False)
        final_box.add(labels_box);
        final_box.add(buttons_box);
        final_box.add(self.labels['tip']);
        final_box.add(distgrid);

        self.content.add(final_box)
        self.layout.show_all()

    def process_update(self, action, data):
        if action == "notify_gcode_response":
            self.on_notify_gcode_response(data)
            return

        if action != "notify_status_update":
            return

        homed_axes = self._screen.printer.get_stat("toolhead", "homed_axes")
        if homed_axes == "xyz":
            if "gcode_move" in data and "gcode_position" in data["gcode_move"]:
                self.labels['pos_z'].set_text("Z: %.2f" % (data["gcode_move"]["gcode_position"][2]))
        else:
            if "z" in homed_axes:
                if "gcode_move" in data and "gcode_position" in data["gcode_move"]:
                    self.labels['pos_z'].set_text("Z: %.2f" % (data["gcode_move"]["gcode_position"][2]))
            else:
                self.labels['pos_z'].set_text("Z: ?")
        return

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

    def on_notify_gcode_response(self, data):
        result = re.match(r"^//\sprobe at.+z=([+\-\d.]+)", data)
        if result:
            z_len = float(result.group(1))
            logging.info("### probe result Z: %0.4f" % (z_len))
            if self.first_tool is None:
                self.first_tool = z_len - self.gcode_base_z
                self.labels["probe1"].set_text("TOOL #1: %0.4f" % (self.first_tool))
                self.labels["tip"].set_text("Step 2: Now change the tool and probe it's height with the Probe button")
            else:
                tool_len = z_len - self.gcode_base_z
                self.labels["probe2"].set_text("TOOL #2: %0.4f" % (tool_len))
                self._screen._ws.klippy.gcode_script("G92 Z%0.4f" % self.first_tool)
                self.labels["tip"].set_text("Done. Press back button")
            
            # Move probe up
            self._screen._ws.klippy.gcode_script("G91\nG1 Z20\nG90")
            return
        result = re.findall(r"^//\sgcode base.+Z:([+\-\d.]+).+$", data, re.MULTILINE)
        if result:
            self.gcode_base_z = float(result[0])
            logging.info("### gcode_base: %0.4f" % (self.gcode_base_z))
