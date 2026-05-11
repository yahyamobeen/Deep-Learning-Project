import 'package:flutter/material.dart';

import 'sign_to_text_screen.dart';
import 'text_to_sign_screen.dart';
import 'speech_to_sign_screen.dart';
import 'tutor_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final tiles = <_Tile>[
      _Tile('Sign → Text',   Icons.video_camera_back, const SignToTextScreen()),
      _Tile('Text → Sign',   Icons.text_fields,        const TextToSignScreen()),
      _Tile('Speech → Sign', Icons.mic,                const SpeechToSignScreen()),
      _Tile('Tutor',         Icons.school,             const TutorScreen()),
    ];

    return Scaffold(
      appBar: AppBar(title: const Text('Sign Language Translator')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: GridView.count(
          crossAxisCount: 2,
          mainAxisSpacing: 16,
          crossAxisSpacing: 16,
          children: tiles.map((t) => _TileCard(tile: t)).toList(),
        ),
      ),
    );
  }
}

class _Tile {
  const _Tile(this.label, this.icon, this.screen);
  final String label;
  final IconData icon;
  final Widget screen;
}

class _TileCard extends StatelessWidget {
  const _TileCard({required this.tile});
  final _Tile tile;

  @override
  Widget build(BuildContext context) {
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => tile.screen)),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(tile.icon, size: 56, color: Theme.of(context).colorScheme.primary),
              const SizedBox(height: 12),
              Text(tile.label, textAlign: TextAlign.center, style: Theme.of(context).textTheme.titleMedium),
            ],
          ),
        ),
      ),
    );
  }
}
