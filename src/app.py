"""Interfaz de línea de comandos del asistente.

    python -m src.app            # chat con el agente (requiere GOOGLE_API_KEY)
    python -m src.app --debug    # muestra herramientas usadas y fragmentos recuperados con su score
"""
import argparse

from src.agent import AgenteAtencion


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="muestra la traza de recuperación")
    args = parser.parse_args()
    agente = AgenteAtencion()
    print("Tecno — Asistente TecnoHogar. Escribe 'salir' para terminar o 'reiniciar' para limpiar la memoria.\n")
    while True:
        consulta = input("Tú: ").strip()
        if not consulta:
            continue
        if consulta.lower() in {"salir", "exit"}:
            break
        if consulta.lower() == "reiniciar":
            agente.memoria.limpiar()
            print("(memoria reiniciada)\n")
            continue
        try:
            r = agente.responder(consulta)
        except Exception as e:  # p. ej. 503 por alta demanda o límite de la capa gratuita
            print(f"\n(No pude contactar al modelo: {str(e)[:160]}. Espera unos segundos y vuelve a intentar.)\n")
            continue
        print(f"\nTecno: {r.texto}\n")
        if args.debug:
            print(f"  [herramientas] {r.herramientas_usadas}")
            for t in r.traza:
                print(f"  [fuente] {t['fuente']} §{t['seccion']} (score={t['score']})")
            print()


if __name__ == "__main__":
    main()
