import Foundation
import ImageIO
import Vision

// Jedna linia JSON na stronę. Obrazy przechodzą przez stdin; nie zapisujemy skanów na dysku.
while let line = readLine() {
    guard let raw = line.data(using: .utf8),
          let item = try? JSONSerialization.jsonObject(with: raw) as? [String: Any],
          let encoded = item["png"] as? String,
          let bytes = Data(base64Encoded: encoded) else {
        fputs("OCR: invalid input\n", stderr)
        print("{}")
        continue
    }
    guard let source = CGImageSourceCreateWithData(bytes as CFData, nil),
          let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
        fputs("OCR: invalid image\n", stderr)
        print("{}")
        continue
    }
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = true
    request.recognitionLanguages = ["pl-PL", "en-US"]
    do {
        try VNImageRequestHandler(cgImage: image).perform([request])
        let lines = (request.results ?? []).compactMap { $0.topCandidates(1).first?.string }
        let result: [String: Any] = ["page": item["page"] ?? 0, "text": lines.joined(separator: "\n")]
        let data = try JSONSerialization.data(withJSONObject: result)
        print(String(decoding: data, as: UTF8.self))
    } catch {
        fputs("OCR: recognition failed: \(error)\n", stderr)
        print("{}")
    }
}
