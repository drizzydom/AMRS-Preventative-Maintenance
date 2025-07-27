#!/bin/bash

# AMRS Deployment Helper
# This script helps deploy the latest fixes for sync system and SocketIO compatibility

echo "🚀 AMRS Deployment Helper"
echo "========================="

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Please run this script from the AMRS project directory"
    exit 1
fi

echo "✅ Current directory: $(pwd)"

# Check current branch
echo ""
echo "📋 Git Status:"
echo "Current branch: $(git branch --show-current)"
git status --porcelain

# Check if we need to merge to main for Render deployment
echo ""
echo "🌿 Branch Analysis:"
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "  ⚠️  Currently on '$CURRENT_BRANCH' branch"
    echo "  ⚠️  Render likely deploys from 'main' branch"
    echo "  🔄 Need to merge fixes to main for deployment"
else
    echo "  ✅ On main branch - ready for Render deployment"
fi

# Show key files that should be deployed
echo ""
echo "🔧 Key files to deploy:"
echo "  - render.yaml (SocketIO-compatible deployment)"
echo "  - wsgi.py (Direct Python execution)"
echo "  - app.py (Fixed sync detection + robust SocketIO configuration)"
echo "  - timezone_utils.py (Centralized detection)"
echo "  - static/js/socket-sync.js (Improved client-side SocketIO handling)"

# Check key configuration
echo ""
echo "🔍 Configuration Check:"

# Check render.yaml
if grep -q "python wsgi.py" render.yaml; then
    echo "  ✅ render.yaml: Using direct Python execution (SocketIO compatible)"
else
    echo "  ❌ render.yaml: Still using gunicorn (will cause socket errors)"
fi

# Check timezone_utils.py detection logic
if grep -A20 "def is_online_server" timezone_utils.py | grep "return" | grep -q "RENDER_EXTERNAL_URL"; then
    echo "  ❌ timezone_utils.py: Still has problematic RENDER_EXTERNAL_URL detection"
else
    echo "  ✅ timezone_utils.py: Uses clean platform detection"
fi

# Check app.py sync detection
if grep -q "is_online_server()" app.py | head -1; then
    echo "  ✅ app.py: Uses centralized detection function"
else
    echo "  ❌ app.py: May have hardcoded detection logic"
fi

echo ""
echo "🔄 Deployment Steps:"
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "  Since you're on '$CURRENT_BRANCH' branch, you need to:"
    echo "  1. Commit current changes: git add . && git commit -m 'Fix sync system and SocketIO compatibility'"
    echo "  2. Switch to main: git checkout main"
    echo "  3. Merge your fixes: git merge $CURRENT_BRANCH"
    echo "  4. Push to trigger Render deployment: git push origin main"
    echo "  5. Monitor Render dashboard for deployment progress"
else
    echo "  1. Commit all changes: git add . && git commit -m 'Fix sync system and SocketIO compatibility'"
    echo "  2. Push to deployment: git push origin main"
fi
echo "  3. Monitor Render logs for: '[SocketIO] Using async_mode: eventlet'"
echo "  4. Test sync: Make changes on online server, check offline client receives SocketIO events"

echo ""
echo "📊 Expected Behavior After Deployment:"
echo "  Online Server:"
echo "    - ✅ No socket errors in logs"
echo "    - ✅ '[SocketIO] Emitting sync event to X clients...' when changes occur"
echo "    - ✅ '[SYNC_QUEUE] Skipping sync queue - this is the online server'"
echo ""
echo "  Offline Client:"
echo "    - ✅ '[SocketIO] Sync event received: Data changed, please sync.'"
echo "    - ✅ '[SYNC_QUEUE] Added update for audit_task_completions:X to sync_queue.'"
echo "    - ✅ '[SYNC] Successfully uploaded and marked X sync_queue items as synced.'"

echo ""
echo "� CRITICAL: Render Start Command Check"
echo "========================================"
echo "❗ The socket errors you're seeing are likely because Render is still"
echo "❗ using 'gunicorn app:app' as the start command instead of 'python wsgi.py'"
echo ""
echo "🔍 TO FIX THIS, YOU MUST:"
echo "1. 🌐 Go to your Render dashboard (https://dashboard.render.com)"
echo "2. 📱 Find your AMRS service"
echo "3. ⚙️  Go to Settings tab"
echo "4. 🔧 Find 'Start Command' field"
echo "5. ✏️  Change it from 'gunicorn app:app' to 'python wsgi.py'"
echo "6. 💾 Save settings"
echo "7. 🚀 Trigger manual deploy or push code changes"
echo ""
echo "📋 Expected start command: python wsgi.py"
echo "❌ Problematic command: gunicorn app:app"
echo ""
echo "💡 Why this matters:"
echo "   - gunicorn doesn't handle SocketIO websockets properly"
echo "   - Causes 'Bad file descriptor' socket errors"
echo "   - Prevents real-time sync notifications from working"
echo "   - wsgi.py uses socketio.run() which handles websockets correctly"

echo ""
echo "🐛 Additional Troubleshooting:"
echo "  After changing start command, if issues persist:"
echo "    - Check Render logs for '[SocketIO] Using async_mode: eventlet'"
echo "    - Ensure no gunicorn processes are mentioned in logs"
echo "    - Verify SocketIO initialization messages appear"
echo "    - Test SocketIO connection from offline client"
echo ""
echo "  SocketIO Connection Issues (offline clients):"
echo "    - Look for 'write() before start_response' errors"
echo "    - Check client console for '[SocketIO] Connection failed' messages"
echo "    - Verify CORS origins include offline client URLs"
echo "    - Check if client is using polling transport before websocket upgrade"
echo "    - Monitor ping/pong messages for connection health"
echo ""
echo "  If offline clients can't connect:"
echo "    - Ensure AMRS_ONLINE_URL in .env points to correct server"
echo "    - Check firewall/network settings allowing SocketIO traffic"
echo "    - Verify server is using 'python wsgi.py' not gunicorn"
echo "    - Test with browser dev tools Network tab for SocketIO requests"

echo ""
echo "✨ IMPORTANT: Deploy code changes AND update Render start command!"
echo "   Both are required to fix the sync system completely."
