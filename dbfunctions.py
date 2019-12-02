import mysql.connector
import datetime
import socket

user = "database_app"
host = socket.gethostbyname("env170519005")
password = ''



class Database:
    def DB(self):
        return mysql.connector.connect(user=user, password=password, database="dewar", host=host)

    def Cursor(self, DB):
        return DB.cursor()

    def Close(self, cursor, DB):
        cursor.close()
        DB.close()

def FindEmptyPositions(Dewar):
    db = mysql.connector.connect(user=user, password=password, database="dewar", host=host)
    cursor = db.cursor()

    query = '''SELECT ID, Cylinder, Cane_Color, Cane_ID, Position FROM dewarupdated 
                    WHERE Available = 'T' AND Dewar = '{}' '''.format(Dewar)
    cursor.execute(query)
    lst_tuples = cursor.fetchall()
    lst_lists = [list(item) for item in lst_tuples]

    return lst_lists

"""def AssignScores(CellType, NumberOfCells, Dewar):
    db = mysql.connector.connect(user=user, password=password, database="dewar", host=host)
    cursor = db.cursor()

    query = '''SELECT ID, Cylinder, Cane_Color, Cane_ID, Position FROM dewarupdated 
                WHERE Available = 'T' AND Dewar = '{}' '''.format(Dewar)
    cursor.execute(query)
    lst = cursor.fetchall()

    for i in range(len(lst)):
        score = 0
        samecellsincylinder = False
        samecellsincane = False
        fullcount = 0
        query = '''SELECT Cells, Dewar, Cylinder, Cane_Color, Cane_ID, Position FROM dewarupdated 
                    WHERE Available = 'F' AND Dewar = '{}' AND Cylinder = '{}' '''.format(Dewar, lst[i][1])
        cursor.execute(query)
        for Cells, Dewar, Cylinder, Cane_Color, Cane_ID, Position in cursor:
            if CellType.lower() in Cells.lower():
                samecellsincylinder = True
            if Cane_Color == lst[i][2] and Cane_ID == lst[i][3] and Position != lst[i][4]:
                if Cells.lower() == CellType.lower():
                    samecellsincane = True
                fullcount += 1

        availablecount = 5 - fullcount
        if samecellsincylinder == True:
            score += 1
        if samecellsincane == True:
            score += 1
        if availablecount >= NumberOfCells:
            score += 1

        lst[i] = list(lst[i])

        lst[i].append(score)
        lst[i].append(availablecount)

    sortingIndexes = [4,3,2,1,6,5]
    for i in sortingIndexes:
        lst = sorted(lst, key = lambda x: x[i], reverse = (i == 5 or i == 6))

    finallst = [x[0:5] for x in lst]
    cursor.close()
    db.close()

    return finallst"""

def CalculateStorage(dewar):
    db = mysql.connector.connect(user=user, password=password, database="dewar", host=host)
    cursor = db.cursor()
    query = "SELECT ID FROM dewarupdated WHERE Dewar = '{}' ".format(dewar)
    cursor.execute(query)
    cursor.fetchall()
    total = str(cursor.rowcount)
    query = "SELECT ID FROM dewarupdated WHERE Dewar = '{}' AND Available = 'T'".format(dewar)
    cursor.execute(query)
    cursor.fetchall()
    available = str(cursor.rowcount)
    cursor.close()
    db.close()
    return "{}/{}".format(available,total)

def StoreCells(Data):
    db = mysql.connector.connect(user=user, password=password, database="dewar", host=host)
    cursor = db.cursor()
    for i in range(len(Data)):

        query = '''UPDATE dewarupdated SET Cells = %s, Passage = %s, Initials = %s, Date=%s, Comments=%s, Available = 'F'
                WHERE ID = %s'''
        cursor.execute(query,((Data[i][1], Data[i][2], Data[i][8], Data[i][9], Data[i][10], Data[i][0])))
        query = '''INSERT INTO logsheet (Cells, Passage, Dewar, Cylinder, Cane_Color, Cane_ID, Position, Initials, Date, Comments, Available)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'F')'''.format(Data[i][1], Data[i][2],
                                                                                             Data[i][3], Data[i][4], Data[i][5], Data[i][6],
                                                                                             Data[i][7], Data[i][8], Data[i][9], Data[i][10])
        cursor.execute(query, (Data[i][1], Data[i][2],Data[i][3], Data[i][4], Data[i][5], Data[i][6], Data[i][7], Data[i][8], Data[i][9], Data[i][10]))
    cursor.close()
    db.commit()


def NewCane(Dewar, Cylinder, Cane_Color, Cane_ID):
    db = mysql.connector.connect(user=user, password=password, database="dewar", host=host)
    cursor = db.cursor()
    for i in range (1,6):
        query = '''INSERT INTO dewarupdated (Dewar, Cylinder, Cane_Color, Cane_ID, Position)
                VALUES ('{}', '{}', '{}', '{}', '{}')'''.format(Dewar, Cylinder, Cane_Color, Cane_ID, i)
        cursor.execute(query)

    query = """SELECT ID, Cylinder, Cane_Color, Cane_ID, Position FROM dewarupdated
                    WHERE Dewar = '{}' AND Cylinder = '{}' AND Cane_Color = '{}' AND Cane_ID = '{}' """.format(Dewar,
                                                                                                             Cylinder,
                                                                                                             Cane_Color,
                                                                                                             Cane_ID)
    cursor.execute(query)
    lst = cursor.fetchall()
    cursor.close()
    db.commit()
    db.close()

    return lst


def FindCompletions(word, cursor):
    query = "SELECT distinct Cells FROM dewarupdated WHERE Cells LIKE '%{}%'".format(word)
    cursor.execute(query)
    lst = []
    for Cells in cursor:
        lst.append(Cells[0])
    return lst

def FindCells(Celltype):
    db = mysql.connector.connect(user=user, password=password, database="dewar", host=host)
    cursor = db.cursor()
    query = """SELECT ID, Cells, Passage, Dewar, Cylinder, Cane_Color, Cane_ID, Position, Initials, Date, Comments FROM dewarupdated
            WHERE Cells LIKE '%{}%' ORDER BY Passage""".format(Celltype)
    cursor.execute(query)
    lst = cursor.fetchall()
    cursor.close()
    db.close()
    return lst

def RetrieveCells(data, trash=False):
    db = mysql.connector.connect(user=user, password=password, database="dewar", host=host)
    cursor= db.cursor()
    todaydate = (datetime.date.today()).strftime("%m/%d/%Y")
    if trash:
        Comment = "Trashed {}".format(todaydate)
    else:
        Comment = "Retreived {}".format(todaydate)
    for item in data:
        query = """UPDATE dewarupdated SET Cells = NULL, Passage = NULL, Initials = NULL, Date = NULL, Comments = NULL,
                Available = 'T' WHERE ID = '{}'""".format(item[0])
        cursor.execute(query)
        query = """UPDATE logsheet SET Comments = CASE
            WHEN Comments is not NULL OR Comments != "" THEN CONCAT(Comments, " - ", %s)
            ELSE %s
        END, Available = 'T'
        WHERE Cells = %s AND Dewar = %s
        AND Cylinder = %s AND Cane_Color = %s AND Cane_ID = %s AND Position = %s AND Date = %s """
        cursor.execute(query, (Comment, Comment, item[1], item[3], item[4], item[5], item[6], item[7], item[9]))
    cursor.close()
    db.commit()
    db.close()

def RetrieveCellLines():
    db = mysql.connector.connect(user=user, password=password, database="dewar", host=host)
    cursor = db.cursor()
    query = "SELECT Cell_Line, Notes FROM celllines"
    cursor.execute(query)
    cellLine = cursor.fetchall()
    cellLine = [list(item) for item in cellLine]
    cellLine.sort(key=lambda x: x[0])
    for line in cellLine:
        query = "SELECT ID FROM dewarupdated WHERE Cells = %s"
        cursor.execute(query, (line[0],))
        cursor.fetchall()
        count = cursor.rowcount
        line.insert(1, count)
    return cellLine

def addNewCellLine(Cell_Line):
    db = mysql.connector.connect(user=user, password=password, database="dewar", host=host)
    cursor = db.cursor()
    query = "INSERT INTO celllines (Cell_Line) VALUES (%s)"
    cursor.execute(query, (Cell_Line,))
    cursor.close()
    db.commit()
    db.close()

def deleteCellLine(Cell_Line):
    db = mysql.connector.connect(user=user, password=password, database="dewar", host=host)
    cursor = db.cursor()
    query = "DELETE FROM celllines WHERE Cell_Line = %s"
    cursor.execute(query, (Cell_Line,))
    cursor.close()
    db.commit()
    db.close()

def editCellLineComment(cell_line, comment):
    db = mysql.connector.connect(user=user, password=password, database="dewar", host=host)
    cursor = db.cursor()
    query = "UPDATE celllines SET Notes = %s WHERE Cell_Line = %s"
    cursor.execute(query, (comment, cell_line))
    cursor.close()
    db.commit()
    db.close()
