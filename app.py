from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from config import Config

import mysql.connector

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

class Autor(db.Model):
    __tablename__ = 'autores'
    id_Autor = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    apellidos = db.Column(db.String(50), nullable=False)

class Libro(db.Model):
    __tablename__ = 'libros'
    id_Libro = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    num_Paginas = db.Column(db.Integer, nullable=False)
    fecha_Publicacion = db.Column(db.String(4), nullable=False)
    editorial = db.Column(db.String(50), nullable=False)
    id_Autor = db.Column(db.Integer, db.ForeignKey('autores.id_Autor'), nullable=False)
    autor = db.relationship('Autor', backref=db.backref('libros', lazy=True))

#Todos los libros
@app.route('/')
def mostrar_libros():
    cur = mysql.connection.cursor()
    cur.execute("SELECT libros.titulo, autores.nombre, autores.apellidos, libros.num_Paginas, libros.fecha_Publicacion, libros.editorial FROM libros INNER JOIN autor_libro ON libros.id_Libro = autor_libro.id_Libro INNER JOIN autores ON autor_libro.id_Autor = autores.id_Autor")
    libros = cur.fetchall()
    cur.close()
    return render_template('index.html', libros=libros)

#Búsqueda
@app.route('/buscar_libros', methods=['GET'])
def buscar_libros():
    query = request.args.get('query', '')
    resultados = Libro.query.join(Autor).filter(
        db.or_(
            Libro.titulo.ilike(f'%{query}%'),
            Autor.nombre.ilike(f'%{query}%'),
            Autor.apellidos.ilike(f'%{query}%')
        )
    ).all()
    return render_template('index.html', resultados_busqueda=resultados, libros=Libro.query.all())

#Editar Registro
@app.route('/editar_libro', methods=['POST'])
def editar_libro():
    titulo = request.form['titulo']
    nombre = request.form['nombre']
    apellidos = request.form['apellidos']
    num_paginas = request.form['num_paginas']
    fecha_publicacion = request.form['fecha_publicacion']
    editorial = request.form['editorial']

    try:
        cursor = db.cursor()
        cursor.execute("""
            UPDATE libros 
            SET titulo=%s, num_Paginas=%s, fecha_Publicacion=%s, editorial=%s 
            WHERE id_Libro=%s
        """, (titulo, num_paginas, fecha_publicacion, editorial, id_libro))

        cursor.execute("""
            UPDATE autores 
            SET nombre=%s, apellidos=%s 
            WHERE id_Autor = (SELECT id_Autor FROM autor_libro WHERE id_Libro=%s)
        """, (nombre, apellidos, id_libro))

        db.commit()
        cursor.close()
        return redirect(url_for('mostrar_libros'))

    except mysql.connector.Error as error:
        print(f"Error al editar libro: {error}")
        db.rollback()

    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()

        return "Error al editar libro"

#Eliminar Registro
@app.route('/eliminar_libro/<int:id_libro>', methods=['DELETE'])
def eliminar_libro(id_libro):
    libro = Libro.query.get(id_libro)
    if libro:
        db.session.delete(libro)
        db.session.commit()
        return jsonify({"success": True}), 200
    return jsonify({"error": "Libro no encontrado"}), 404

#Registrar libro
@app.route('/agregar_libro', methods=['POST'])
def agregar_libro():
    data = request.form
    nuevo_libro = Libro(
        titulo=data['titulo'],
        num_Paginas=data['num_paginas'],
        fecha_Publicacion=data['fecha_publicacion'],
        editorial=data['editorial'],
        id_Autor=data['autor_id']
    )
    db.session.add(nuevo_libro)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/agregar_autor', methods=['POST'])
def agregar_autor():
    data = request.form
    nuevo_autor = Autor(nombre=data['nombre'], apellidos=data['apellidos'])
    db.session.add(nuevo_autor)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
