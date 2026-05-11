import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiClient {
  ApiClient._() {
    final base = dotenv.maybeGet('GATEWAY_URL') ?? 'http://10.0.2.2:4000';
    dio = Dio(BaseOptions(
      baseUrl: base,
      connectTimeout: const Duration(seconds: 15),
      sendTimeout: const Duration(seconds: 60),
      receiveTimeout: const Duration(seconds: 60),
    ));
    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: 'jwt');
        if (token != null && token.isNotEmpty) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
    ));
  }

  static final ApiClient instance = ApiClient._();
  late final Dio dio;
  final _storage = const FlutterSecureStorage();

  // ---- Translate ---------------------------------------------------------
  Future<Map<String, dynamic>> signToText(File videoFile) async {
    final form = FormData.fromMap({
      'file': await MultipartFile.fromFile(videoFile.path, filename: 'sign.mp4'),
    });
    final r = await dio.post('/api/translate/sign-to-text', data: form);
    return Map<String, dynamic>.from(r.data as Map);
  }

  Future<Map<String, dynamic>> textToSign(String text) async {
    final r = await dio.post('/api/translate/text-to-sign', data: {'text': text});
    return Map<String, dynamic>.from(r.data as Map);
  }

  Future<Map<String, dynamic>> speechToSign(File audioFile) async {
    final form = FormData.fromMap({
      'file': await MultipartFile.fromFile(audioFile.path, filename: 'audio.m4a'),
    });
    final r = await dio.post('/api/translate/speech-to-sign', data: form);
    return Map<String, dynamic>.from(r.data as Map);
  }

  // ---- Tutor -------------------------------------------------------------
  Future<List<Map<String, dynamic>>> tutorLessons() async {
    final r = await dio.get('/api/tutor/lessons');
    return (r.data as List).map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  Future<Map<String, dynamic>> tutorScore(String lessonId, File attempt) async {
    final form = FormData.fromMap({
      'lesson_id': lessonId,
      'file': await MultipartFile.fromFile(attempt.path, filename: 'attempt.mp4'),
    });
    final r = await dio.post('/api/tutor/score', data: form);
    return Map<String, dynamic>.from(r.data as Map);
  }

  // ---- Auth --------------------------------------------------------------
  Future<void> setToken(String token) => _storage.write(key: 'jwt', value: token);
  Future<void> clearToken() => _storage.delete(key: 'jwt');
  Future<String?> readToken() => _storage.read(key: 'jwt');
}
