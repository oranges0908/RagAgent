import 'package:flutter/material.dart';
import '../services/api_service.dart';

class PapersPage extends StatefulWidget {
  const PapersPage({super.key});
  @override
  State<PapersPage> createState() => _PapersPageState();
}

class _PapersPageState extends State<PapersPage> {
  List<Paper>? _papers;
  String? _error;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final papers = await ApiService.getPapers();
      setState(() => _papers = papers);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text('论文列表', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
              const Spacer(),
              IconButton(onPressed: _load, icon: const Icon(Icons.refresh), tooltip: '刷新'),
            ],
          ),
          const SizedBox(height: 24),
          if (_loading)
            const Center(child: CircularProgressIndicator())
          else if (_error != null)
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.red.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.red),
              ),
              child: Text(_error!, style: TextStyle(color: Colors.red.shade800)),
            )
          else if (_papers == null || _papers!.isEmpty)
            const Center(child: Text('暂无论文，请先上传 PDF。'))
          else
            Expanded(
              child: ListView.separated(
                itemCount: _papers!.length,
                separatorBuilder: (context, index) => const SizedBox(height: 8),
                itemBuilder: (context, i) {
                  final p = _papers![i];
                  return Card(
                    child: ListTile(
                      leading: const Icon(Icons.article_outlined),
                      title: Text(p.title, style: const TextStyle(fontWeight: FontWeight.bold)),
                      subtitle: Text('${p.filename}  •  ${p.chunkCount} chunks'),
                      trailing: _StatusChip(p.status),
                    ),
                  );
                },
              ),
            ),
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  final String status;
  const _StatusChip(this.status);

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      'ready' => Colors.green,
      'processing' => Colors.orange,
      'error' => Colors.red,
      String() => Colors.grey,
    };
    return Chip(
      label: Text(status, style: TextStyle(color: color, fontSize: 12)),
      backgroundColor: color.withValues(alpha: 0.1),
      side: BorderSide(color: color),
      padding: EdgeInsets.zero,
    );
  }
}
