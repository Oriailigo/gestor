from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from flask import send_file
import io
import json
import uuid
import os

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # Máx 2 MB por imagen
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
    # Aquí añades el filtrado 
    buscar = request.args.get("buscar", "").lower()
    precio_min = request.args.get("precio_min")
    precio_max = request.args.get("precio_max")
    unidades_min = request.args.get("unidades_min")
    unidades_max = request.args.get("unidades_max")

    filtrados = []

    for p in productos:
        if buscar and buscar not in p["nombre"].lower():
            continue
        if precio_min and p["precio"] < float(precio_min):
            continue
        if precio_max and p["precio"] > float(precio_max):
            continue
        if unidades_min and p["unidades"] < int(unidades_min):
            continue
        if unidades_max and p["unidades"] > int(unidades_max):
            continue
        filtrados.append(p)

    return render_template("index.html", productos=filtrados)


@app.route("/agregar", methods=["POST"])
def agregar():
    productos = cargar_productos()
    nombre = request.form["nombre"]

    if any(p["nombre"].lower() == nombre.lower() for p in productos):
        return "Producto ya existente", 400

    imagen = request.files.get("imagen")
    nombre_imagen = None

    if imagen and imagen.filename != "":
        filename = secure_filename(imagen.filename)
        ruta_imagen = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        imagen.save(ruta_imagen)
        nombre_imagen = filename

    nuevo = {
        "id": str(uuid.uuid4()),
        "nombre": nombre,
        "unidades": int(request.form["unidades"]),
        "precio": float(request.form["precio"]),
        "imagen": nombre_imagen  # Guardamos el nombre de archivo
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

        imagen = request.files.get("imagen")
        if imagen and imagen.filename != "":
            from werkzeug.utils import secure_filename
            ext = os.path.splitext(imagen.filename)[1]
            filename = f"{uuid.uuid4().hex}{ext}"
            ruta_imagen = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            imagen.save(ruta_imagen)

            # 🗑️ Eliminar la imagen anterior si existe
            imagen_anterior = producto.get("imagen")
            if imagen_anterior:
                ruta_anterior = os.path.join(app.config["UPLOAD_FOLDER"], imagen_anterior)
                if os.path.exists(ruta_anterior):
                    os.remove(ruta_anterior)

            producto["imagen"] = filename


        guardar_productos(productos)
        return redirect(url_for("index"))

    return render_template("editar.html", producto=producto)

@app.route("/eliminar/<id>")
def eliminar(id):
    productos = cargar_productos()
    productos = [p for p in productos if p["id"] != id]
    guardar_productos(productos)
    return redirect(url_for("index"))

from flask import send_file
import io

@app.route("/subir_json", methods=["POST"])
def subir_json():
    if "jsonfile" not in request.files:
        return "No se envió ningún archivo", 400
    file = request.files["jsonfile"]
    if file.filename == "":
        return "Archivo no seleccionado", 400
    if not file.filename.endswith(".json"):
        return "Solo se permiten archivos JSON", 400
    
    try:
        data = json.load(file)
    except Exception:
        return "Archivo JSON inválido", 400

    productos = cargar_productos()

    # Validar y agregar productos nuevos sin duplicados por nombre
    nombres_existentes = {p["nombre"].lower() for p in productos}
    nuevos = 0
    for prod in data:
        if "nombre" in prod and prod["nombre"].lower() not in nombres_existentes:
            # Añadimos id si no tiene
            prod.setdefault("id", str(uuid.uuid4()))
            productos.append(prod)
            nombres_existentes.add(prod["nombre"].lower())
            nuevos += 1

    guardar_productos(productos)
    return f"Se agregaron {nuevos} productos nuevos.", 200


@app.route("/descargar_json")
def descargar_json():
    productos = cargar_productos()
    contenido = json.dumps(productos, indent=4, ensure_ascii=False)
    buffer = io.BytesIO()
    buffer.write(contenido.encode('utf-8'))
    buffer.seek(0)
    return send_file(buffer,
                     as_attachment=True,
                     download_name="productos_actualizados.json",
                     mimetype="application/json")


if __name__ == "__main__":
    app.run(debug=True)


