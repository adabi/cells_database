from mysql.connector import connect
from collections import Counter

db = connect(user = "root", password="password", database="Dewar")
cursor = db.cursor()
query = '''SELECT Dewar, Cylinder, Cane_Color, Cane_ID FROM dewarupdatedGR'''
cursor.execute(query)
list1 = cursor.fetchall()
toAdd = []
for i in Counter(list1):
    if Counter(list1)[i] < 5:
        toAdd.append(i)

print(toAdd)

fullist = [1,2,3,4,5]

for i in toAdd:
    occupied = []
    query = '''SELECT Dewar, Cylinder, Cane_Color, Cane_ID, Position FROM dewarupdatedGR
            WHERE Dewar = "{}" AND Cylinder = "{}" AND Cane_Color = "{}" AND Cane_ID = "{}"'''.format(i[0], i[1], i[2], i[3])
    cursor.execute(query)
    rows = cursor.fetchall()
    for row in rows:
        occupied.append(row[4])
    final = list(fullist)
    for j in occupied:
            final.remove(j)
    for j in final:
        query = '''INSERT INTO dewarupdatedGR (Dewar, Cylinder, Cane_Color, Cane_ID, Position)
                VALUES ("{}", "{}", "{}", "{}", "{}") '''.format(i[0], i[1], i[2], i[3], j)
        cursor.execute(query)

db.commit()
cursor.close()
db.close()



