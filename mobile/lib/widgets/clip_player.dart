import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:video_player/video_player.dart';

/// Plays one or more clip URLs returned by `/translate/text-to-sign`.
/// Relative paths (e.g. `/static/clips/hello.mp4`) are resolved against
/// the gateway base URL.
class ClipPlayer extends StatefulWidget {
  const ClipPlayer({super.key, required this.clipUrls});
  final List<String> clipUrls;

  @override
  State<ClipPlayer> createState() => _ClipPlayerState();
}

class _ClipPlayerState extends State<ClipPlayer> {
  VideoPlayerController? _ctrl;
  int _idx = 0;

  @override
  void initState() {
    super.initState();
    _load(0);
  }

  String _resolve(String url) {
    if (url.startsWith('http')) return url;
    final base = dotenv.maybeGet('GATEWAY_URL') ?? '';
    return '$base$url';
  }

  Future<void> _load(int i) async {
    final old = _ctrl;
    if (i >= widget.clipUrls.length) {
      old?.dispose();
      if (mounted) setState(() { _ctrl = null; _idx = i; });
      return;
    }
    final c = VideoPlayerController.networkUrl(Uri.parse(_resolve(widget.clipUrls[i])));
    await c.initialize();
    c.addListener(() {
      if (c.value.position >= c.value.duration && !c.value.isPlaying) {
        _load(i + 1);
      }
    });
    await c.play();
    old?.dispose();
    if (mounted) setState(() { _ctrl = c; _idx = i; });
  }

  @override
  void dispose() { _ctrl?.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    final c = _ctrl;
    if (widget.clipUrls.isEmpty) return const Text('No clips to play.');
    if (c == null || !c.value.isInitialized) {
      return const SizedBox(height: 200, child: Center(child: CircularProgressIndicator()));
    }
    return Column(
      children: [
        AspectRatio(aspectRatio: c.value.aspectRatio, child: VideoPlayer(c)),
        const SizedBox(height: 8),
        Text('Clip ${_idx + 1} / ${widget.clipUrls.length}'),
      ],
    );
  }
}
