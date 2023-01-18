def sql_insert(con, entities):
    cur = con.cursor()
    cur.execute(
        """INSERT INTO score(Nickname, Score, Coin) VALUES(?, ?, ?)""",
        entities)
    con.commit()


def sql_update_score(con, entities):
    cur = con.cursor()
    cur.execute("""UPDATE score
                   SET Score = ?
                   WHERE Nickname = ?""",
                entities)
    con.commit()


def sql_update_coin(con, entities):
    cur = con.cursor()
    cur.execute("""UPDATE score
                   SET Coin = ?
                   WHERE Nickname = ?""",
                entities)
    con.commit()
