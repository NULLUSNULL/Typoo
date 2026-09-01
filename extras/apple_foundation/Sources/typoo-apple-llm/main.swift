// typoo-apple-llm — ayudante que conecta Typoo con Apple Foundation Models.
//
// Protocolo (lo usa ai/proveedores.py → _stream_apple):
//   • Entrada (stdin): UNA línea JSON:
//       {"messages":[{"role":"system|user|assistant","content":"…"}],
//        "temperature":0.7, "max_tokens":1024}
//   • Salida (stdout): el texto de la respuesta EN STREAMING (fragmentos), sin
//     envoltura; se escribe y vacía a medida que se genera.
//   • Errores: mensaje en stderr y código de salida != 0.
//
// Requisitos: macOS 26+ (Tahoe), Apple Silicon y Apple Intelligence activado.
//
// NOTA: la API de FoundationModels puede variar entre versiones del SDK; si al
// compilar cambia alguna firma, ajusta las llamadas señaladas más abajo.

import Foundation

#if canImport(FoundationModels)
import FoundationModels
#endif

struct Mensaje: Codable { let role: String; let content: String }
struct Peticion: Codable {
    let messages: [Mensaje]
    let temperature: Double?
    let max_tokens: Int?
}

func fallar(_ mensaje: String) -> Never {
    FileHandle.standardError.write(Data((mensaje + "\n").utf8))
    exit(1)
}

func emitir(_ texto: String) {
    guard !texto.isEmpty else { return }
    FileHandle.standardOutput.write(Data(texto.utf8))
}

// ─── Leer la petición de stdin ───────────────────────────────────────────────
let entrada = FileHandle.standardInput.readDataToEndOfFile()
guard let peticion = try? JSONDecoder().decode(Peticion.self, from: entrada) else {
    fallar("Petición JSON inválida.")
}

let instrucciones = peticion.messages
    .filter { $0.role == "system" }
    .map { $0.content }
    .joined(separator: "\n")

let conversacion = peticion.messages
    .filter { $0.role != "system" }
    .map { ($0.role == "assistant" ? "Asistente: " : "Autor: ") + $0.content }
    .joined(separator: "\n")
let prompt = conversacion.isEmpty ? " " : conversacion

#if canImport(FoundationModels)
if #available(macOS 26.0, *) {
    // Comprobar disponibilidad del modelo del sistema.
    let modelo = SystemLanguageModel.default
    switch modelo.availability {
    case .available:
        break
    case .unavailable(let motivo):
        fallar("Apple Intelligence no disponible: \(motivo)")
    @unknown default:
        fallar("Apple Intelligence no disponible.")
    }

    // Ejecutar la generación en streaming.
    let sem = DispatchSemaphore(value: 0)
    Task {
        do {
            let session = LanguageModelSession(instructions: instrucciones)
            var opciones = GenerationOptions()
            if let t = peticion.temperature { opciones = GenerationOptions(temperature: t) }

            // streamResponse entrega instantáneas acumuladas; emitimos el delta.
            var emitido = ""
            let flujo = session.streamResponse(to: prompt, options: opciones)
            for try await parcial in flujo {
                // `parcial.content` es el texto acumulado hasta el momento.
                let actual = parcial.content
                if actual.count > emitido.count {
                    let inicio = actual.index(actual.startIndex, offsetBy: emitido.count)
                    emitir(String(actual[inicio...]))
                    emitido = actual
                }
            }
        } catch {
            FileHandle.standardError.write(Data(("Error de generación: \(error)\n").utf8))
            exit(1)
        }
        sem.signal()
    }
    sem.wait()
    exit(0)
} else {
    fallar("Se requiere macOS 26 o superior.")
}
#else
fallar("Este binario debe compilarse en macOS con el SDK de FoundationModels.")
#endif
