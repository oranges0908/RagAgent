import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../services/api_service.dart';

/// Renders [text] with [keywords] highlighted in yellow.
class _HighlightedText extends StatelessWidget {
  final String text;
  final List<String> keywords;

  const _HighlightedText({required this.text, required this.keywords});

  @override
  Widget build(BuildContext context) {
    final filtered = keywords.where((k) => k.length > 2).toList();
    if (filtered.isEmpty) {
      return Text(text,
          style: const TextStyle(fontSize: 13, color: Colors.black87));
    }

    final pattern = RegExp(
      filtered.map(RegExp.escape).join('|'),
      caseSensitive: false,
    );

    final spans = <TextSpan>[];
    int last = 0;
    for (final match in pattern.allMatches(text)) {
      if (match.start > last) {
        spans.add(TextSpan(text: text.substring(last, match.start)));
      }
      spans.add(TextSpan(
        text: text.substring(match.start, match.end),
        style: const TextStyle(
          backgroundColor: Color(0xFFFFEB3B),
          fontWeight: FontWeight.bold,
        ),
      ));
      last = match.end;
    }
    if (last < text.length) {
      spans.add(TextSpan(text: text.substring(last)));
    }

    return Text.rich(
      TextSpan(
        style: const TextStyle(fontSize: 13, color: Colors.black87),
        children: spans,
      ),
    );
  }
}

class QueryPage extends StatefulWidget {
  const QueryPage({super.key});
  @override
  State<QueryPage> createState() => _QueryPageState();
}

class _QueryPageState extends State<QueryPage> {
  final _questionCtrl = TextEditingController();
  bool _loading = false;
  String? _error;

  // Streaming state
  String _answer = '';
  List<Source> _sources = [];

  // Paper selector state
  List<Paper> _papers = [];
  String? _selectedPaperId; // null = 全库

  StreamSubscription<Map<String, dynamic>>? _streamSub;

  @override
  void initState() {
    super.initState();
    _loadPapers();
  }

  Future<void> _loadPapers() async {
    try {
      final papers = await ApiService.getPapers();
      setState(() => _papers = papers);
    } catch (_) {
      // Non-critical
    }
  }

  Future<void> _submit() async {
    final q = _questionCtrl.text.trim();
    if (q.isEmpty) return;

    await _streamSub?.cancel();
    setState(() {
      _loading = true;
      _error = null;
      _answer = '';
      _sources = [];
    });

    _streamSub = ApiService.queryStream(q, paperId: _selectedPaperId).listen(
      (event) {
        final type = event['type'] as String;
        if (type == 'sources') {
          setState(() {
            _sources = (event['sources'] as List)
                .map((s) => Source.fromJson(s as Map<String, dynamic>))
                .toList();
          });
        } else if (type == 'delta') {
          setState(() => _answer += event['text'] as String);
        } else if (type == 'done') {
          setState(() => _loading = false);
        }
      },
      onError: (e) {
        setState(() {
          _error = e.toString();
          _loading = false;
        });
      },
      onDone: () {
        setState(() => _loading = false);
      },
    );
  }

  @override
  void dispose() {
    _streamSub?.cancel();
    _questionCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('论文问答',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),
          // Paper selector dropdown
          DropdownButtonFormField<String?>(
            initialValue: _selectedPaperId,
            decoration: const InputDecoration(
              labelText: '检索范围',
              border: OutlineInputBorder(),
              contentPadding:
                  EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            ),
            items: [
              const DropdownMenuItem<String?>(
                value: null,
                child: Text('全库'),
              ),
              ..._papers.map((p) => DropdownMenuItem<String?>(
                    value: p.id,
                    child:
                        Text(p.title, overflow: TextOverflow.ellipsis),
                  )),
            ],
            onChanged: (v) => setState(() => _selectedPaperId = v),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _questionCtrl,
                  decoration: const InputDecoration(
                    hintText: '输入你的问题…',
                    border: OutlineInputBorder(),
                  ),
                  onSubmitted: (_) => _submit(),
                ),
              ),
              const SizedBox(width: 12),
              ElevatedButton(
                onPressed: _loading ? null : _submit,
                child: _loading
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child:
                            CircularProgressIndicator(strokeWidth: 2))
                    : const Text('提问'),
              ),
            ],
          ),
          const SizedBox(height: 24),
          if (_error != null)
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.red.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.red),
              ),
              child: Text(_error!,
                  style: TextStyle(color: Colors.red.shade800)),
            ),
          if (_answer.isNotEmpty || _sources.isNotEmpty) ...[
            const Text('答案',
                style: TextStyle(
                    fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.grey.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.grey.shade300),
              ),
              child: MarkdownBody(data: _answer),
            ),
            if (_sources.isNotEmpty) ...[
              const SizedBox(height: 20),
              const Text('来源',
                  style: TextStyle(
                      fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              ..._sources.asMap().entries.map((e) {
                final i = e.key;
                final s = e.value;
                return Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ExpansionTile(
                    initiallyExpanded: false,
                    tilePadding: const EdgeInsets.symmetric(horizontal: 12),
                    childrenPadding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
                    title: Text(
                      '[${i + 1}] ${s.section}  •  score: ${s.score.toStringAsFixed(3)}',
                      style: const TextStyle(
                          fontWeight: FontWeight.bold, fontSize: 13),
                    ),
                    children: [
                      _HighlightedText(
                        text: s.text,
                        keywords: _questionCtrl.text.trim().split(RegExp(r'\s+')),
                      ),
                    ],
                  ),
                );
              }),
            ],
          ],
        ],
      ),
    );
  }
}
