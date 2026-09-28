import Foundation
import AVFoundation

// The audio device owns the timeline. The terminal consumes currentTime.
do {
    guard CommandLine.arguments.count > 1 else { throw NSError(domain: "Missing audio path", code: 1) }
    let player = try AVAudioPlayer(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1]))
    player.prepareToPlay()
    player.volume = 0.75
    var quitting = false
    var pending = ""
    let input = FileHandle.standardInput
    input.readabilityHandler = { handle in
        let data = handle.availableData
        DispatchQueue.main.async {
            if data.isEmpty { quitting = true; return }
            pending += String(decoding: data, as: UTF8.self)
            while let newline = pending.firstIndex(of: "\n") {
                let line = String(pending[..<newline])
                pending.removeSubrange(...newline)
                let fields = line.split(separator: " ")
                switch fields.first {
                case "play":
                    if !player.play() {
                        FileHandle.standardOutput.write(Data("{\"error\":\"Audio output unavailable\"}\n".utf8))
                    }
                case "pause": player.pause()
                case "seek":
                    if fields.count > 1, let t = Double(fields[1]) {
                        player.currentTime = min(max(0, t), max(0, player.duration - 0.01))
                    }
                case "volume":
                    if fields.count > 1, let v = Float(fields[1]) { player.volume = min(1, max(0, v)) }
                case "quit": quitting = true
                default: break
                }
            }
        }
    }
    while !quitting {
        RunLoop.current.run(until: Date(timeIntervalSinceNow: 1.0 / 60.0))
        let line = String(format: "{\"time\":%.6f,\"duration\":%.6f,\"playing\":%@}\n",
                          player.currentTime, player.duration, player.isPlaying ? "true" : "false")
        FileHandle.standardOutput.write(Data(line.utf8))
    }
    input.readabilityHandler = nil
    player.stop()
} catch {
    FileHandle.standardError.write(Data("Audio error: \(error.localizedDescription)\n".utf8))
    exit(1)
}
