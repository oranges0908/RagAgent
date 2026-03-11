import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'dart:convert';

const String _baseUrl = 'http://localhost:8000';

class Source {
  final String paperId;
  final String section;
  final int chunkIndex;
  final String text;
  final double score;

  Source({
    required this.paperId,
    required this.section,
    required this.chunkIndex,
    required this.text,
    required this.score,
  });

  factory Source.fromJson(Map<String, dynamic> j) => Source(
        paperId: j['paper_id'],
        section: j['section'],
        chunkIndex: j['chunk_index'],
        text: j['text'],
        score: (j['score'] as num).toDouble(),
      );
}

class QueryResponse {
  final String answer;
  final List<Source> sources;
  QueryResponse({required this.answer, required this.sources});
}

class Paper {
  final String id;
  final String title;
  final String filename;
  final int chunkCount;
  final String status;
  Paper({
    required this.id,
    required this.title,
    required this.filename,
    required this.chunkCount,
    required this.status,
  });
  factory Paper.fromJson(Map<String, dynamic> j) => Paper(
        id: j['id'],
        title: j['title'],
        filename: j['filename'],
        chunkCount: j['chunk_count'],
        status: j['status'],
      );
}

class ApiService {
  /// 上传 PDF，返回 Paper 元数据
  static Future<Paper> upload(String filename, Uint8List bytes) async {
    final req = http.MultipartRequest('POST', Uri.parse('$_baseUrl/api/upload'));
    req.files.add(http.MultipartFile.fromBytes('file', bytes, filename: filename));
    final streamed = await req.send();
    final body = await streamed.stream.bytesToString();
    if (streamed.statusCode != 200) {
      final detail = jsonDecode(body)['detail'] ?? body;
      throw Exception('Upload failed: $detail');
    }
    return Paper.fromJson(jsonDecode(body));
  }

  /// 获取所有论文列表（按上传时间降序）
  static Future<List<Paper>> getPapers() async {
    final res = await http.get(Uri.parse('$_baseUrl/api/papers'));
    if (res.statusCode != 200) {
      throw Exception('Failed to load papers: ${res.body}');
    }
    final list = jsonDecode(res.body) as List;
    return list.map((j) => Paper.fromJson(j)).toList();
  }

  /// 问答，paper_id 为 null 时跨全库检索
  static Future<QueryResponse> query(String question, {String? paperId}) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/api/query'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'question': question, 'paper_id': paperId}),
    );
    if (res.statusCode != 200) {
      final detail = jsonDecode(res.body)['detail'] ?? res.body;
      throw Exception('Query failed: $detail');
    }
    final data = jsonDecode(res.body);
    return QueryResponse(
      answer: data['answer'],
      sources: (data['sources'] as List).map((s) => Source.fromJson(s)).toList(),
    );
  }
}
