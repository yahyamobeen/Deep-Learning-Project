import 'dart:io';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:path_provider/path_provider.dart';

/// Records up to [maxSeconds] of video and returns the file via [onRecorded].
class CameraRecorder extends StatefulWidget {
  const CameraRecorder({super.key, required this.onRecorded, this.maxSeconds = 3});
  final ValueChanged<File> onRecorded;
  final int maxSeconds;

  @override
  State<CameraRecorder> createState() => _CameraRecorderState();
}

class _CameraRecorderState extends State<CameraRecorder> {
  CameraController? _controller;
  bool _initialising = true;
  bool _recording = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    final cam = await Permission.camera.request();
    final mic = await Permission.microphone.request();
    if (!cam.isGranted || !mic.isGranted) {
      setState(() { _error = 'Camera/microphone permission denied.'; _initialising = false; });
      return;
    }
    final cameras = await availableCameras();
    if (cameras.isEmpty) {
      setState(() { _error = 'No camera available on this device.'; _initialising = false; });
      return;
    }
    final front = cameras.firstWhere(
      (c) => c.lensDirection == CameraLensDirection.front,
      orElse: () => cameras.first,
    );
    final ctrl = CameraController(front, ResolutionPreset.medium, enableAudio: false);
    await ctrl.initialize();
    setState(() { _controller = ctrl; _initialising = false; });
  }

  Future<void> _startStop() async {
    final ctrl = _controller;
    if (ctrl == null) return;
    if (_recording) return;
    setState(() => _recording = true);
    try {
      await ctrl.startVideoRecording();
      await Future<void>.delayed(Duration(seconds: widget.maxSeconds));
      final XFile clip = await ctrl.stopVideoRecording();
      // Persist to a stable temp path
      final dir = await getTemporaryDirectory();
      final dest = File('${dir.path}/sign_${DateTime.now().millisecondsSinceEpoch}.mp4');
      await File(clip.path).copy(dest.path);
      widget.onRecorded(dest);
    } catch (e) {
      _error = 'Recording failed: $e';
    } finally {
      if (mounted) setState(() => _recording = false);
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_initialising) return const Center(child: CircularProgressIndicator());
    if (_error != null) return Center(child: Text(_error!, textAlign: TextAlign.center));
    final ctrl = _controller;
    if (ctrl == null) return const SizedBox.shrink();

    return Column(
      children: [
        AspectRatio(aspectRatio: ctrl.value.aspectRatio, child: CameraPreview(ctrl)),
        const SizedBox(height: 12),
        FilledButton.icon(
          onPressed: _recording ? null : _startStop,
          icon: Icon(_recording ? Icons.fiber_manual_record : Icons.videocam),
          label: Text(_recording ? 'Recording…' : 'Record ${widget.maxSeconds}s'),
        ),
      ],
    );
  }
}
