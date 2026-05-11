import 'package:flutter/material.dart';

import '../api/api_client.dart';
import '../widgets/clip_player.dart';

class TextToSignScreen extends StatefulWidget {
  const TextToSignScreen({super.key});

  @override
  State<TextToSignScreen> createState() => _TextToSignScreenState();
}

class _TextToSignScreenState extends State<TextToSignScreen> {
  final _ctrl = TextEditingController(text: 'i am hungry');
  bool _busy = false;
  List<String> _gloss = const [];
  List<String> _clips = const [];
  String? _error;

  Future<void> _go() async {
    final text = _ctrl.text.trim();
    if (text.isEmpty) return;
    setState(() { _busy = true; _error = null; _gloss = const []; _clips = const []; });
    try {
      final r = await ApiClient.instance.textToSign(text);
      setState(() {
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
  void dispose() { _ctrl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('English Text → Sign')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _ctrl,
              decoration: const InputDecoration(border: OutlineInputBorder(), labelText: 'English sentence'),
              minLines: 1, maxLines: 3,
            ),
            const SizedBox(height: 12),
            FilledButton.icon(onPressed: _busy ? null : _go, icon: const Icon(Icons.translate), label: const Text('Translate')),
            const SizedBox(height: 16),
            if (_busy) const LinearProgressIndicator(),
            if (_error != null) Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
            if (_gloss.isNotEmpty) ...[
              Text('Gloss: ${_gloss.join(" ")}', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 12),
              ClipPlayer(clipUrls: _clips),
            ],
          ],
        ),
      ),
    );
  }
}
