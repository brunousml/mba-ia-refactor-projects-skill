from models import admin_model


def resetar():
    admin_model.resetar()


def executar(sql):
    return admin_model.executar(sql)
