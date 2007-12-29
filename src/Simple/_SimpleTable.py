#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2007  Donald N. Allingham
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""
Provides a simplified table creation interface
"""

import copy

import gen.lib
import Errors
import DateHandler

class SimpleTable:
    """
    Provides a simplified table creation interface.
    """

    def __init__(self, access, doc, title=None):
        """
        Initializes the class with a simpledb, and simpledoc
        """
        self.access = access
        self.simpledoc = doc # simpledoc; simpledoc.doc = docgen object
        self.title = title
        self.__columns = []
        self.__rows = []
        self.__link = []
        self.__sort_col = None
        self.__sort_reverse = False

    def get_row_count(self):
        return len(self.__rows)

    def columns(self, *columns):
        """
        Set the columns
        """
        self.__columns = list(copy.copy(columns))

    def on_table_doubleclick(self, obj, path, view_column):
        """
        Handle events on tables. obj is a treeview
        """
        from Editors import EditPerson, EditEvent
        selection = obj.get_selection()
        store, node = selection.get_selected()
        if not node:
            return
        index = store.get_value(node, 0) # index
        if self.__link[index]:
            htype, handle = self.__link[index]
            if htype == 'Person':
                person = self.access.dbase.get_person_from_handle(handle)
                try:
                    EditPerson(self.simpledoc.doc.dbstate, 
                               self.simpledoc.doc.uistate, [], person)
                    return True # handled event
                except Errors.WindowActiveError:
                    pass
            elif htype == 'Event':
                event = self.access.dbase.get_event_from_handle(handle)
                try:
                    EditEvent(self.simpledoc.doc.dbstate, 
                              self.simpledoc.doc.uistate, [], event)
                    return True # handled event
                except Errors.WindowActiveError:
                    pass
        return False # didn't handle event

    def on_table_click(self, obj):
        """
        Handle events on tables. obj is a treeview
        """
        selection = obj.get_selection()
        store, node = selection.get_selected()
        if not node:
            return
        index = store.get_value(node, 0) # index
        if self.__link[index]:
            htype, handle = self.__link[index]
            if htype == 'Person':
                person = self.access.dbase.get_person_from_handle(handle)
                self.simpledoc.doc.dbstate.change_active_person(person)
                return True
            elif htype == 'Event':
                pass
        return False # didn't handle event

    def row(self, *data):
        """
        Add a row of data.
        """
        retval = [] 
        link   = None
        for item in data:
            if type(item) in [str, unicode]:
                retval.append(item)
            elif isinstance(item, gen.lib.Person):
                name = self.access.name(item)
                retval.append(name)
                link = ('Person', item.handle)
            elif isinstance(item, gen.lib.Family): pass
            elif isinstance(item, gen.lib.Source): pass
            elif isinstance(item, gen.lib.Event):
                name = self.access.event_type(item)
                retval.append(name)
                link = ('Event', item.handle)
            elif isinstance(item, gen.lib.MediaObject): pass
            elif isinstance(item, gen.lib.Place): pass
            elif isinstance(item, gen.lib.Repository): pass
            elif isinstance(item, gen.lib.Note): pass
            elif isinstance(item, gen.lib.Date):
                text = DateHandler.displayer.display(item)
                retval.append(text)
                #link = ('Date', item)
            else:
                raise AttributeError, ("unknown object type: '%s': %s" % 
                                       (item, type(item)))
        self.__link.append(link)
        self.__rows.append(retval)

    def sort(self, column_name, reverse=False):
        self.__sort_col = column_name
        self.__sort_reverse = reverse

    def __sort(self):
        idx = self.__columns.index(self.__sort_col)
        if self.__sort_reverse:
            self.__rows.sort(lambda a, b: -cmp(a[idx],b[idx]))
        else:
            self.__rows.sort(lambda a, b: cmp(a[idx],b[idx]))

    def write(self):
        if self.simpledoc.doc.type == "standard":
            doc = self.simpledoc.doc
            doc.start_table('simple','Table')
            columns = len(self.__columns)
            if self.title:
                doc.start_row()
                doc.start_cell('TableHead',columns)
                doc.start_paragraph('TableTitle')
                doc.write_text(_(self.title))
                doc.end_paragraph()
                doc.end_cell()
                doc.end_row()
            if self.__sort_col:
                self.__sort()
            doc.start_row()
            for col in self.__columns:
                doc.start_cell('TableNormalCell',1)
                doc.write_text(col,'TableTitle')
                doc.end_cell()
            doc.end_row()
            for row in self.__rows:
                doc.start_row()
                for col in row:
                    doc.start_cell('TableNormalCell',1)
                    doc.write_text(col,'Normal')
                    doc.end_cell()
                doc.end_row()
            doc.end_table()
            doc.start_paragraph("Normal")
            doc.end_paragraph()
        elif self.simpledoc.doc.type == "gtk":
            import gtk
            buffer = self.simpledoc.doc.buffer
            text_view = self.simpledoc.doc.text_view
            model_index = 1 # start after index
            if self.__sort_col:
                sort_index = self.__columns.index(self.__sort_col)
            else:
                sort_index = 0
            treeview = gtk.TreeView()
            treeview.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)
            treeview.connect('row-activated', self.on_table_doubleclick)
            treeview.connect('cursor-changed', self.on_table_click)
            renderer = gtk.CellRendererText()
            types = [int] # index
            for col in self.__columns:
                types.append(type(col))
                column = gtk.TreeViewColumn(col,renderer,text=model_index)
                column.set_sort_column_id(model_index)
                treeview.append_column(column)
                #if model_index == sort_index:
                # FIXME: what to set here?    
                model_index += 1
            if self.title:
                self.simpledoc.paragraph(self.title)
            # Make a GUI to put the tree view in
            frame = gtk.Frame()
            frame.add(treeview)
            model = gtk.ListStore(*types)
            treeview.set_model(model)
            iter = buffer.get_end_iter()
            anchor = buffer.create_child_anchor(iter)
            text_view.add_child_at_anchor(frame, anchor)
            count = 0
            for data in self.__rows:
                model.append(row=([count] + list(data)))
                count += 1
            frame.show_all()
            self.simpledoc.paragraph("")
            self.simpledoc.paragraph("")
