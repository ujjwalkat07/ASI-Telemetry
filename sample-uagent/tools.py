--- a/sample-uagent/tools.py
+++ b/sample-uagent/tools.py
@@ -32,2 +32,2 @@
-    completion_tokens = payload["completion_tokens"]
+    completion_tokens = payload.get("completion_tokens", 0)
