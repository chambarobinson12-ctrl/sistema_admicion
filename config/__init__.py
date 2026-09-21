# Usamos PyMySQL como reemplazo de mysqlclient porque mysqlclient necesita
# compilar C++ (requiere Visual C++ Build Tools en Windows). PyMySQL es
# 100% Python y no necesita compilación.
import pymysql
pymysql.install_as_MySQLdb()
pymysql.version_info = (2, 2, 4, "final", 0)
