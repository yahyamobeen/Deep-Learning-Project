import 'dart:io';

import 'package:flutter/material.dart';

import '../api/api_client.dart';
import '../widgets/camera_recorder.dart';

class SignToTextScreen extends StatefulWidget {
  const SignToTextScreen({super.key});

  @override
  State<SignToTextScreen> createState() => _SignToTextScreenState();
}

class _SignToTextScreenState extends State<SignToTextScreen> {
  bool _busy = false;
  String? _gloss;
  String? _sentence;
  double? _confidence;
  List<String>? _top5;
  String? _error;

  Future<void> _submit(File clip) async {
    setState(() { _busy = true; _error = null; _gloss = null; _sentence = null; });
    try {
      final r = await ApiClient.instance.signToText(clip);
      setState(() {
        _gloss      = r['gloss'] as String?;
        _sentence   = r['sentence'] as String?;
        _confidence = (r['confidence'] as num?)?.toDouble();
        _top5       = (r['top5'] as List?)?.map((e) => e.toString()).toList();
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
      appBar: AppBar(title: const Text('Sign → English Text')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            CameraRecorder(onRecorded: _submit),
            const SizedBox(height: 16),
            if (_busy) const LinearProgressIndicator(),
            if (_error != null) Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
            if (_sentence != null) Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(_sentence!, style: Theme.of(context).textTheme.headlineSmall),
                    const SizedBox(height: 8),
                    Text('Gloss: $_gloss', style: Theme.of(context).textTheme.titleMedium),
                    if (_confidence != null) Text('Confidence: ${(_confidence! * 100).toStringAsFixed(1)}%'),
                    if (_top5 != null) Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Text('Top-5: ${_top5!.join(", ")}'),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
