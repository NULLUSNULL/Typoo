// swift-tools-version: 6.0
// Paquete del ayudante que expone el modelo de Apple Foundation a Typoo.
// Compilar en macOS con Apple Intelligence:  swift build -c release
// El binario queda en .build/release/typoo-apple-llm

import PackageDescription

let package = Package(
    name: "typoo-apple-llm",
    platforms: [
        .macOS("26.0")   // Foundation Models requiere macOS 26 (Tahoe) o superior
    ],
    targets: [
        .executableTarget(
            name: "typoo-apple-llm",
            path: "Sources/typoo-apple-llm"
        )
    ]
)
