import 'package:flutter/material.dart';

final ColorScheme _light = ColorScheme.fromSeed(seedColor: const Color(0xFF4F46E5));
final ColorScheme _dark  = ColorScheme.fromSeed(seedColor: const Color(0xFF4F46E5), brightness: Brightness.dark);

final ThemeData appLightTheme = ThemeData(
  useMaterial3: true,
  colorScheme: _light,
  appBarTheme: const AppBarTheme(centerTitle: true, elevation: 0),
);

final ThemeData appDarkTheme = ThemeData(
  useMaterial3: true,
  colorScheme: _dark,
  appBarTheme: const AppBarTheme(centerTitle: true, elevation: 0),
);
