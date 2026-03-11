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
  String? _deletingId;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _confirmDelete(Paper paper) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('确认删除'),
        content: Text('删除「${paper.title}」？此操作不可撤销。'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('取消')),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('删除'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    setState(() => _deletingId = paper.id);
    try {
      await ApiService.deletePaper(paper.id);
      await _load();
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _deletingId = null);
    }
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
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          _StatusChip(p.status),
                          const SizedBox(width: 8),
                          _deletingId == p.id
                              ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(strokeWidth: 2))
                              : IconButton(
                                  icon: const Icon(Icons.delete_outline, color: Colors.red),
                                  tooltip: '删除',
                                  onPressed: () => _confirmDelete(p),
                                ),
                        ],
                      ),
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
