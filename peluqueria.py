from dataclasses import dataclass, asdict
from datetime import datetime
import csv
import os


CLIENTES_FILE = "clientes.csv"
TURNOS_FILE = "turnos.csv"


@dataclass
class Cliente:
    dni: str
    nombre: str
    telefono: str


@dataclass
class Turno:
    id_turno: int
    dni_cliente: str
    fecha: str  # YYYY-MM-DD
    hora: str   # HH:MM
    servicio: str
    estado: str = "ACTIVO"  # ACTIVO / CANCELADO


class Peluqueria:
    def __init__(self):
        # "Base de datos" en memoria
        self.clientes: dict[str, Cliente] = {}
        self.turnos: dict[int, Turno] = {}
        self.next_id = 1
        # Al iniciar, intento cargar datos desde CSV
        self.cargar_datos()

    # ----------------- Persistencia -----------------
    def cargar_datos(self):
        """Carga clientes y turnos desde los CSV, si existen."""
        if os.path.exists(CLIENTES_FILE):
            with open(CLIENTES_FILE, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cliente = Cliente(
                        dni=row["dni"],
                        nombre=row["nombre"],
                        telefono=row["telefono"],
                    )
                    self.clientes[cliente.dni] = cliente

        if os.path.exists(TURNOS_FILE):
            with open(TURNOS_FILE, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                max_id = 0
                for row in reader:
                    turno = Turno(
                        id_turno=int(row["id_turno"]),
                        dni_cliente=row["dni_cliente"],
                        fecha=row["fecha"],
                        hora=row["hora"],
                        servicio=row["servicio"],
                        estado=row.get("estado", "ACTIVO"),
                    )
                    self.turnos[turno.id_turno] = turno
                    if turno.id_turno > max_id:
                        max_id = turno.id_turno
                self.next_id = max_id + 1

    def guardar_datos(self):
        """Guarda el contenido de los dicts en los CSV."""
        with open(CLIENTES_FILE, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["dni", "nombre", "telefono"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for cliente in self.clientes.values():
                writer.writerow(asdict(cliente))

        with open(TURNOS_FILE, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["id_turno", "dni_cliente", "fecha", "hora", "servicio", "estado"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for turno in self.turnos.values():
                writer.writerow(asdict(turno))

    # ----------------- Utilidades -----------------
    @staticmethod
    def pedir_fecha():
        while True:
            fecha_str = input("Ingrese la fecha (DD/MM/AAAA): ")
            try:
                fecha = datetime.strptime(fecha_str, "%d/%m/%Y").date()
                return fecha
            except ValueError:
                print("Fecha inválida. Intente nuevamente.")

    @staticmethod
    def pedir_hora():
        while True:
            hora_str = input("Ingrese la hora (HH:MM, formato 24hs): ")
            try:
                hora = datetime.strptime(hora_str, "%H:%M").time()
                return hora
            except ValueError:
                print("Hora inválida. Intente nuevamente.")

    def turno_ocupado(self, fecha, hora):
        """Valida que no haya dos turnos activos en el mismo horario."""
        for turno in self.turnos.values():
            if (
                turno.estado == "ACTIVO"
                and turno.fecha == fecha.isoformat()
                and turno.hora == hora.strftime("%H:%M")
            ):
                return True
        return False

    # ----------------- Operaciones de negocio -----------------
    def registrar_cliente(self):
        print("\n--- Registrar nuevo cliente ---")
        dni = input("DNI: ").strip()
        if dni in self.clientes:
            print("Ya existe un cliente con ese DNI.")
            return
        nombre = input("Nombre completo: ").strip()
        telefono = input("Teléfono: ").strip()

        cliente = Cliente(dni=dni, nombre=nombre, telefono=telefono)
        self.clientes[dni] = cliente
        self.guardar_datos()
        print("Cliente registrado con éxito.\n")

    def solicitar_turno(self):
        print("\n--- Solicitar turno ---")
        if not self.clientes:
            print("No hay clientes cargados. Primero registre un cliente.")
            return

        dni = input("Ingrese DNI del cliente: ").strip()
        if dni not in self.clientes:
            print("No existe un cliente con ese DNI.")
            return

        fecha = self.pedir_fecha()
        hora = self.pedir_hora()

        if self.turno_ocupado(fecha, hora):
            print("Ya existe un turno activo en esa fecha y hora.")
            return

        servicio = input("Servicio (corte, color, etc.): ").strip()
        turno = Turno(
            id_turno=self.next_id,
            dni_cliente=dni,
            fecha=fecha.isoformat(),
            hora=hora.strftime("%H:%M"),
            servicio=servicio,
        )
        self.turnos[turno.id_turno] = turno
        self.next_id += 1
        self.guardar_datos()
        print(f"Turno registrado con ID {turno.id_turno}.\n")

    def listar_turnos(self):
        print("\n--- Listar turnos ---")
        if not self.turnos:
            print("No hay turnos cargados.\n")
            return

        print("1) Listar todos")
        print("2) Filtrar por DNI de cliente")
        print("3) Filtrar por fecha")
        opcion = input("Seleccione una opción: ").strip()

        turnos_a_mostrar = list(self.turnos.values())

        if opcion == "2":
            dni = input("DNI: ").strip()
            turnos_a_mostrar = [t for t in turnos_a_mostrar if t.dni_cliente == dni]
        elif opcion == "3":
            fecha = self.pedir_fecha().isoformat()
            turnos_a_mostrar = [t for t in turnos_a_mostrar if t.fecha == fecha]

        if not turnos_a_mostrar:
            print("No se encontraron turnos con ese criterio.\n")
            return

        # Ordenar por fecha y hora
        turnos_a_mostrar.sort(key=lambda t: (t.fecha, t.hora))

        for t in turnos_a_mostrar:
            cliente = self.clientes.get(t.dni_cliente)
            nombre = cliente.nombre if cliente else "Desconocido"
            print(
                f"ID: {t.id_turno} | Cliente: {nombre} ({t.dni_cliente}) | "
                f"Fecha: {t.fecha} {t.hora} | Servicio: {t.servicio} | Estado: {t.estado}"
            )
        print()

    def modificar_o_cancelar_turno(self):
        print("\n--- Modificar o cancelar turno ---")
        if not self.turnos:
            print("No hay turnos cargados.\n")
            return

        try:
            id_turno = int(input("Ingrese el ID del turno: "))
        except ValueError:
            print("ID inválido.")
            return

        turno = self.turnos.get(id_turno)
        if not turno:
            print("No existe un turno con ese ID.")
            return

        print(
            f"Turno seleccionado: {turno.id_turno} - Fecha {turno.fecha} {turno.hora} "
            f"- Servicio: {turno.servicio} - Estado: {turno.estado}"
        )
        print("1) Modificar fecha y hora")
        print("2) Modificar servicio")
        print("3) Cancelar turno")
        opcion = input("Opción: ").strip()

        if opcion == "1":
            fecha = self.pedir_fecha()
            hora = self.pedir_hora()
            if self.turno_ocupado(fecha, hora):
                print("Ya existe un turno activo en esa fecha y hora.")
                return
            turno.fecha = fecha.isoformat()
            turno.hora = hora.strftime("%H:%M")
        elif opcion == "2":
            turno.servicio = input("Nuevo servicio: ").strip()
        elif opcion == "3":
            turno.estado = "CANCELADO"
        else:
            print("Opción no válida.")
            return

        self.guardar_datos()
        print("Turno actualizado.\n")

    # ----------------- Menú principal -----------------
    def ejecutar(self):
        while True:
            print("==== Sistema de turnos para peluquería ====")
            print("1) Registrar nuevo cliente")
            print("2) Solicitar turno")
            print("3) Listar turnos existentes")
            print("4) Modificar o cancelar turno")
            print("5) Guardar datos en CSV")
            print("6) Salir")
            opcion = input("Seleccione una opción: ").strip()

            if opcion == "1":
                self.registrar_cliente()
            elif opcion == "2":
                self.solicitar_turno()
            elif opcion == "3":
                self.listar_turnos()
            elif opcion == "4":
                self.modificar_o_cancelar_turno()
            elif opcion == "5":
                self.guardar_datos()
                print("Datos guardados en CSV.\n")
            elif opcion == "6":
                print("Saliendo del sistema...")
                break
            else:
                print("Opción no válida.\n")


if __name__ == "__main__":
    sistema = Peluqueria()
    sistema.ejecutar()
