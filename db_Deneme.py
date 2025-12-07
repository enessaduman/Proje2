from falkordb import FalkorDB

db = FalkorDB(host='localhost', port=6379)
graph = db.select_graph("RECIPIES") # Graph adının doğru olduğundan emin ol

print("--- TARİF İLİŞKİLERİ ---")
# Tarifler hangi ilişkiyle neye bağlanıyor?
res = graph.query("MATCH (r:Recipe)-[rel]->(n) RETURN distinct type(rel), labels(n)")
for row in res.result_set:
    print(row)

print("\n--- 'MILK' İÇEREN MALZEMELER ---")
# Veritabanında içinde 'milk' geçen neler var?
res2 = graph.query("MATCH (i:Ingredient) WHERE toLower(i.name) CONTAINS 'milk' RETURN i.name")
for row in res2.result_set:
    print(row)