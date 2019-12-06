# Cells database

This app manages a database of cells with options to store and retrieve cells and browse the storage dewar.

Currently the app requires a MySQL database on the local network. The database must contain a dewarupdated table with the following columns:
[ID, Cells, Passage, Dewar, Cylinder, Cane_Color, Cane_ID, Position, Initials, Date, Comments, Available(Takes on values of T or F)]

The following features are under construction:
- Automatic update from gitrelease for MacOS and Windows
- Custom table structure
- CSV backup of database

The interface is constructed using the Qt toolkit, the source code for which can be found at: https://github.com/qt/qtbase
