"Функция, для появления новой записи в базах данных"


def sql_insert(con, entities):
    cur = con.cursor()
    cur.execute(
        """INSERT INTO score(Nickname, Score, Coin, spaceX2, spaceX3, spaceX4) VALUES(?, ?, ?, ?, ?, ?)""",
        entities)
    con.commit()


"Функция, для обновления количества очков"


def sql_update_score(con, entities):
    cur = con.cursor()
    cur.execute("""UPDATE score
                   SET Score = ?
                   WHERE Nickname = ?""",
                entities)
    con.commit()


"Функция, для обновления количества монет"


def sql_update_coin(con, entities):
    cur = con.cursor()
    cur.execute("""UPDATE score
                   SET Coin = ?
                   WHERE Nickname = ?""",
                entities)
    con.commit()
