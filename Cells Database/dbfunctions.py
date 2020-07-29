import mysql.connector
import datetime

SQL_DB = None
SQL_CURSOR = None


def login_with_credentials(username, password, database, host):

    global SQL_DB
    global SQL_CURSOR

    try:
        SQL_DB = mysql.connector.connect(user=username, password=password, database=database, host=host)
        SQL_CURSOR = SQL_DB.cursor()
    except Exception as e:
        print(e)

    if SQL_DB and SQL_CURSOR:
        return True
    else:
        return False



def FindEmptyPositions(Dewar):
    query = '''SELECT ID, Cylinder, Cane_Color, Cane_ID, Position FROM dewarupdated 
                    WHERE Available = 'T' AND Dewar = '{}' '''.format(Dewar)
    SQL_CURSOR.execute(query)
    lst_tuples = SQL_CURSOR.fetchall()
    lst_lists = [list(item) for item in lst_tuples]

    return lst_lists


def CalculateStorage(dewar):

    query = "SELECT ID FROM dewarupdated WHERE Dewar = '{}' ".format(dewar)
    SQL_CURSOR.execute(query)
    SQL_CURSOR.fetchall()
    total = str(SQL_CURSOR.rowcount)
    query = "SELECT ID FROM dewarupdated WHERE Dewar = '{}' AND Available = 'T'".format(dewar)
    SQL_CURSOR.execute(query)
    SQL_CURSOR.fetchall()
    available = str(SQL_CURSOR.rowcount)
    return "{}/{}".format(available,total)

def StoreCells(Data):

    for i in range(len(Data)):

        query = '''UPDATE dewarupdated SET Cells = %s, Passage = %s, Initials = %s, Date=%s, Comments=%s, Available = 'F'
                WHERE ID = %s'''
        SQL_CURSOR.execute(query,((Data[i][1], Data[i][2], Data[i][8], Data[i][9], Data[i][10], Data[i][0])))
        query = '''INSERT INTO logsheet (Cells, Passage, Dewar, Cylinder, Cane_Color, Cane_ID, Position, Initials, Date, Comments, Available)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'F')'''.format(Data[i][1], Data[i][2],
                                                                                             Data[i][3], Data[i][4], Data[i][5], Data[i][6],
                                                                                             Data[i][7], Data[i][8], Data[i][9], Data[i][10])
        SQL_CURSOR.execute(query, (Data[i][1], Data[i][2],Data[i][3], Data[i][4], Data[i][5], Data[i][6], Data[i][7], Data[i][8], Data[i][9], Data[i][10]))
    SQL_DB.commit()


def NewCane(Dewar, Cylinder, Cane_Color, Cane_ID):

    for i in range (1,6):
        query = '''INSERT INTO dewarupdated (Dewar, Cylinder, Cane_Color, Cane_ID, Position)
                VALUES ('{}', '{}', '{}', '{}', '{}')'''.format(Dewar, Cylinder, Cane_Color, Cane_ID, i)
        SQL_CURSOR.execute(query)

    query = """SELECT ID, Cylinder, Cane_Color, Cane_ID, Position FROM dewarupdated
                    WHERE Dewar = '{}' AND Cylinder = '{}' AND Cane_Color = '{}' AND Cane_ID = '{}' """.format(Dewar,
                                                                                                             Cylinder,
                                                                                                             Cane_Color,
                                                                                                             Cane_ID)
    SQL_CURSOR.execute(query)
    lst = SQL_CURSOR.fetchall()
    SQL_DB.commit()

    return lst

def FindCompletions(word):
    query = "SELECT distinct Cells FROM dewarupdated WHERE Cells LIKE '%{}%'".format(word)
    SQL_CURSOR.execute(query)
    lst = []
    for Cells in SQL_CURSOR:
        lst.append(Cells[0])
    return lst

def FindCells(Celltype):

    query = """SELECT ID, Cells, Passage, Dewar, Cylinder, Cane_Color, Cane_ID, Position, Initials, Date, Comments FROM dewarupdated
            WHERE Cells LIKE '%{}%' ORDER BY Passage""".format(Celltype)
    SQL_CURSOR.execute(query)
    lst = SQL_CURSOR.fetchall()

    return lst

def RetrieveCells(data, trash=False):

    todaydate = (datetime.date.today()).strftime("%m/%d/%Y")
    if trash:
        Comment = "Trashed {}".format(todaydate)
    else:
        Comment = "Retreived {}".format(todaydate)
    for item in data:
        query = """UPDATE dewarupdated SET Cells = NULL, Passage = NULL, Initials = NULL, Date = NULL, Comments = NULL,
                Available = 'T' WHERE ID = '{}'""".format(item[0])
        SQL_CURSOR.execute(query)
        query = """UPDATE logsheet SET Comments = CASE
            WHEN Comments is not NULL OR Comments != "" THEN CONCAT(Comments, " - ", %s)
            ELSE %s
        END, Available = 'T'
        WHERE Cells = %s AND Dewar = %s
        AND Cylinder = %s AND Cane_Color = %s AND Cane_ID = %s AND Position = %s AND Date = %s """
        SQL_CURSOR.execute(query, (Comment, Comment, item[1], item[3], item[4], item[5], item[6], item[7], item[9]))
    SQL_DB.commit()


def RetrieveCellLines():
    query = "SELECT Cell_Line, Notes FROM celllines"
    SQL_CURSOR.execute(query)
    cellLine = SQL_CURSOR.fetchall()
    cellLine = [list(item) for item in cellLine]
    cellLine.sort(key=lambda x: x[0])
    for line in cellLine:
        query = "SELECT ID FROM dewarupdated WHERE Cells = %s"
        SQL_CURSOR.execute(query, (line[0],))
        SQL_CURSOR.fetchall()
        count = SQL_CURSOR.rowcount
        line.insert(1, count)
    return cellLine

def addNewCellLine(Cell_Line):

    query = "INSERT INTO celllines (Cell_Line) VALUES (%s)"
    SQL_CURSOR.execute(query, (Cell_Line,))
    SQL_DB.commit()


def deleteCellLine(Cell_Line):

    query = "DELETE FROM celllines WHERE Cell_Line = %s"
    SQL_CURSOR.execute(query, (Cell_Line,))
    SQL_DB.commit()


def editCellLineComment(cell_line, comment):

    query = "UPDATE celllines SET Notes = %s WHERE Cell_Line = %s"
    SQL_CURSOR.execute(query, (comment, cell_line))
    SQL_DB.commit()


def retrieve_for_cylinder_population(dewar):
    query = '''Select Cells, Passage, Cylinder, Cane_Color, Cane_ID, Position, Initials, Date, Comments, Available
                  FROM dewarupdated WHERE Dewar = %s'''
    SQL_CURSOR.execute(query, (dewar,))
    return SQL_CURSOR.fetchall()


def retrieve_for_backup():
    query = '''Select Dewar, Cells, Passage, Cylinder, Cane_Color, Cane_ID, Position, Initials, Date, Comments 
    FROM dewarupdated'''
    SQL_CURSOR.execute(query)
    return SQL_CURSOR.fetchall()

def execute_sql_query(query):
    SQL_CURSOR.execute(query)

def commit_to_db():
    SQL_DB.commit()

def close_db_connection():
    SQL_CURSOR.close()
    SQL_DB.close()
