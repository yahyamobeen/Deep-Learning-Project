import 'dart:io';

import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:record/record.dart';

import '../api/api_client.dart';
import '../widgets/clip_player.dart';

class SpeechToSignScreen extends StatefulWidget {
  const SpeechToSignScreen({super.key});

  @override
  State<SpeechToSignScreen> createState() => _SpeechToSignScreenState();
}

class _SpeechToSignScreenState extends State<SpeechToSignScreen> {
  final _recorder = AudioRecorder();
  bool _recording = false;
  bool _busy = false;
  String? _path;
  String? _transcript;
  List<String> _gloss = const [];
  List<String> _clips = const [];
  String? _error;

  Future<void> _toggleRecord() async {
    if (_recording) {
      final p = await _recorder.stop();
      setState(() { _recording = false; _path = p; });
      if (p != null) await _send(File(p));
      return;
    }
    if (!await Permission.microphone.request().isGranted) {
      setState(() => _error = 'Microphone permission denied.');
      return;
    }
    final dir = await getTemporaryDirectory();
    final out = '${dir.path}/audio_${DateTime.now().millisecondsSinceEpoch}.m4a';
    await _recorder.start(const RecordConfig(encoder: AudioEncoder.aacLc), path: out);
    setState(() { _recording = true; _path = out; _error = null; });
  }

  Future<void> _send(File audio) async {
    setState(() { _busy = true; _transcript = null; _gloss = const []; _clips = const []; });
    try {
      final r = await ApiClient.instance.speechToSign(audio);
      setState(() {
        _transcript = r['transcript'] as String?;
        _gloss = (r['gloss'] as List).map((e) => e.toString()).toList();
        _clips = (r['clips'] as List).map((e) => e.toString()).toList();
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  void dispose() { _recorder.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('English Speech → Sign')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            FilledButton.icon(
              onPressed: _busy ? null : _toggleRecord,
              icon: Icon(_recording ? Icons.stop : Icons.mic),
              label: Text(_recording ? 'Stop & Translate' : 'Record'),
            ),
            const SizedBox(height: 16),
            if (_busy) const LinearProgressIndicator(),
            if (_error != null) Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
            if (_transcript != null) Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Text('Heard: $_transcript', style: Theme.of(context).textTheme.titleMedium),
            ),
            if (_gloss.isNotEmpty) ...[
              Text('Gloss: ${_gloss.join(" ")}'),
              const SizedBox(height: 12),
              ClipPlayer(clipUrls: _clips),
            ],
          ],
        ),
      ),
    );
  }
}
