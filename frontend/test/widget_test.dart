import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/main.dart';

void main() {
  testWidgets('App renders upload and query tabs', (WidgetTester tester) async {
    await tester.pumpWidget(const RagAgentApp());
    expect(find.text('上传'), findsOneWidget);
    expect(find.text('问答'), findsOneWidget);
  });
}
