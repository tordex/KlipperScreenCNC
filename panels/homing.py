import gi
import logging

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

from ks_includes.KlippyGcodes import KlippyGcodes
from ks_includes.screen_panel import ScreenPanel

def create_panel(*args):
    return MovePanel(*args)

class MovePanel(ScreenPanel):

    def initialize(self, panel_name):
        _ = self.lang.gettext

        grid = self._gtk.HomogeneousGrid()

        self.labels['home'] = self._gtk.ButtonImage("home", _("Home All"), "color4")
        self.labels['home'].connect("clicked", self.home)

        self.labels['home-xy'] = self._gtk.ButtonImage("home", _("Home XY"), "color4")
        self.labels['home-xy'].connect("clicked", self.homexy)

        self.labels['z_tilt'] = self._gtk.ButtonImage("z-tilt", _("Z Tilt"), "color4")
        self.labels['z_tilt'].connect("clicked", self.z_tilt)

        self.labels['quad_gantry_level'] = self._gtk.ButtonImage("z-tilt", _("Quad Gantry Level"), "color4")
        self.labels['quad_gantry_level'].connect("clicked", self.quad_gantry_level)

        self.labels['x'] = self._gtk.ButtonImage("home-x", _("X+"), "color1")
        self.labels['x'].connect("clicked", self.homex)

        self.labels['y'] = self._gtk.ButtonImage("home-y", _("Y+"), "color2")
        self.labels['y'].connect("clicked", self.homey)

        self.labels['z'] = self._gtk.ButtonImage("home-z", _("Z+"), "color3")
        self.labels['z'].connect("clicked", self.homez)

        grid.attach(self.labels['home'], 0, 0, 1, 1)
        grid.attach(self.labels['home-xy'], 1, 0, 1, 1)
        if self._printer.config_section_exists("z_tilt"):
            grid.attach(self.labels['z_tilt'], 2, 0, 1, 1)
        elif self._printer.config_section_exists("quad_gantry_level"):
            grid.attach(self.labels['quad_gantry_level'], 2, 0, 1, 1)
        grid.attach(self.labels['x'], 0, 1, 1, 1)
        grid.attach(self.labels['y'], 1, 1, 1, 1)
        grid.attach(self.labels['z'], 2, 1, 1, 1)


        bottomgrid = self._gtk.HomogeneousGrid()
        self.labels['pos_x'] = Gtk.Label("X: ?")
        self.labels['pos_y'] = Gtk.Label("Y: ?")
        self.labels['pos_z'] = Gtk.Label("Z: ?")
        bottomgrid.attach(self.labels['pos_x'], 0, 0, 1, 1)
        bottomgrid.attach(self.labels['pos_y'], 1, 0, 1, 1)
        bottomgrid.attach(self.labels['pos_z'], 2, 0, 1, 1)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.pack_start(grid, True, True, 0)
        box.pack_end(bottomgrid, True, True, 10)

        self.content.add(box)

    def process_update(self, action, data):
        if action != "notify_status_update":
            return

        homed_axes = self._screen.printer.get_stat("toolhead", "homed_axes")
        if homed_axes == "xyz":
            if "toolhead" in data and "position" in data["toolhead"]:
                self.labels['pos_x'].set_text("X: %.2f" % (data["toolhead"]["position"][0]))
                self.labels['pos_y'].set_text("Y: %.2f" % (data["toolhead"]["position"][1]))
                self.labels['pos_z'].set_text("Z: %.2f" % (data["toolhead"]["position"][2]))
        else:
            if "x" in homed_axes:
                if "toolhead" in data and "position" in data["toolhead"]:
                    self.labels['pos_x'].set_text("X: %.2f" % (data["toolhead"]["position"][0]))
            else:
                self.labels['pos_x'].set_text("X: ?")
            if "y"  in homed_axes:
                if "toolhead" in data and "position" in data["toolhead"]:
                    self.labels['pos_y'].set_text("Y: %.2f" % (data["toolhead"]["position"][1]))
            else:
                self.labels['pos_y'].set_text("Y: ?")
            if "z" in homed_axes:
                if "toolhead" in data and "position" in data["toolhead"]:
                    self.labels['pos_z'].set_text("Z: %.2f" % (data["toolhead"]["position"][2]))
            else:
                self.labels['pos_z'].set_text("Z: ?")
