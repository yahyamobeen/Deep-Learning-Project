import 'dart:io';

import 'package:flutter/material.dart';

import '../api/api_client.dart';
import '../widgets/camera_recorder.dart';

class TutorScreen extends StatefulWidget {
  const TutorScreen({super.key});

  @override
  State<TutorScreen> createState() => _TutorScreenState();
}

class _TutorScreenState extends State<TutorScreen> {
  late Future<List<Map<String, dynamic>>> _lessonsFuture;
  Map<String, dynamic>? _selected;
  bool _busy = false;
  double? _score;
  String? _hint;
  bool? _passed;
  String? _error;

  @override
  void initState() {
    super.initState();
    _lessonsFuture = ApiClient.instance.tutorLessons();
  }

  Future<void> _submitAttempt(File clip) async {
    final lesson = _selected;
    if (lesson == null) return;
    setState(() { _busy = true; _error = null; _score = null; });
    try {
      final r = await ApiClient.instance.tutorScore(lesson['id'] as String, clip);
      setState(() {
        _score  = (r['score']  as num).toDouble();
        _hint   = r['hint']   as String?;
        _passed = r['passed'] as bool?;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Tutor')),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _lessonsFuture,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) {
            return Padding(padding: const EdgeInsets.all(16), child: Text('Failed: ${snap.error}'));
          }
          final lessons = snap.data ?? const [];
          final selected = _selected;
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text('Pick a lesson', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8, runSpacing: 8,
                children: lessons.map((l) {
                  final id = l['id'] as String;
                  final isSel = selected != null && selected['id'] == id;
                  return ChoiceChip(
                    label: Text(l['label'] as String),
                    selected: isSel,
                    onSelected: (_) => setState(() {
                      _selected = l;
                      _score = null; _hint = null; _passed = null; _error = null;
                    }),
                  );
                }).toList(),
              ),
              const SizedBox(height: 24),
              if (selected != null) ...[
                Text('Now record your attempt:', style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 8),
                CameraRecorder(onRecorded: _submitAttempt),
                const SizedBox(height: 16),
                if (_busy) const LinearProgressIndicator(),
                if (_error != null) Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
                if (_score != null) Card(
                  color: (_passed ?? false) ? Colors.green.shade50 : Colors.orange.shade50,
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Score: ${_score!.toStringAsFixed(1)} / 100',
                             style: Theme.of(context).textTheme.headlineSmall),
                        if (_hint != null) Padding(padding: const EdgeInsets.only(top: 8), child: Text(_hint!)),
                      ],
                    ),
                  ),
                ),
              ],
            ],
          );
        },
      ),
    );
  }
}
