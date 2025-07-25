from flask import Flask, render_template, request, redirect, url_for
import json
import uuid
import os

app = Flask(__name__)
ARCHIVO = "productos.json"

def cargar_productos():
    if os.path.exists(ARCHIVO):
        with open(ARCHIVO, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def guardar_productos(productos):
    with open(ARCHIVO, 'w', encoding='utf-8') as f:
        json.dump(productos, f, indent=4, ensure_ascii=False)

@app.route("/")
def index():
    productos = cargar_productos()
    return render_template("index.html", productos=productos)

@app.route("/agregar", methods=["POST"])
def agregar():
    productos = cargar_productos()
    nombre = request.form["nombre"]

    if any(p["nombre"].lower() == nombre.lower() for p in productos):
        return "Producto ya existente", 400

    nuevo = {
        "id": str(uuid.uuid4()),
        "nombre": nombre,
        "unidades": int(request.form["unidades"]),
        "precio": float(request.form["precio"])
    }
    productos.append(nuevo)
    guardar_productos(productos)
    return redirect(url_for("index"))

@app.route("/editar/<id>", methods=["GET", "POST"])
def editar(id):
    productos = cargar_productos()
    producto = next((p for p in productos if p["id"] == id), None)

    if not producto:
        return "Producto no encontrado", 404

    if request.method == "POST":
        producto["nombre"] = request.form["nombre"]
        producto["unidades"] = int(request.form["unidades"])
        producto["precio"] = float(request.form["precio"])
        guardar_productos(productos)
        return redirect(url_for("index"))

    return render_template("editar.html", producto=producto)

@app.route("/eliminar/<id>")
def eliminar(id):
    productos = cargar_productos()
    productos = [p for p in productos if p["id"] != id]
    guardar_productos(productos)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
