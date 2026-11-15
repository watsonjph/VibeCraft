#!/usr/bin/env bash
# Harness for driving the VibeCraft dev dedicated server through its console.
# Usage: vc.sh launch | doctor | send <console command> | wait-log <regex> [seconds] | evidence <name> | daemon [args] | stop
set -u
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
RUN="$ROOT/run"
STATE="$RUN/verify"
LOG="$RUN/logs/latest.log"
PORT=25599

alive() { [ -f "$STATE/$1.pid" ] && kill -0 "$(cat "$STATE/$1.pid")" 2>/dev/null; }

wait_log() { # regex, seconds
	local i=0
	while [ "$i" -lt "${2:-60}" ]; do
		grep -Eq "$1" "$LOG" 2>/dev/null && return 0
		sleep 1; i=$((i + 1))
	done
	echo "timed out after ${2:-60}s waiting for: $1" >&2
	return 1
}

case "${1:-}" in
launch)
	if alive server; then echo "already running (pid $(cat "$STATE/server.pid")); run stop first" >&2; exit 1; fi
	mkdir -p "$STATE" "$RUN/logs"
	# Verification scaffolding: accept the EULA and move off the default port so a
	# real server on 25565 is never touched. Offline mode: no Mojang login needed.
	echo "eula=true" > "$RUN/eula.txt"
	[ -f "$RUN/server.properties" ] || printf 'server-port=%s\nonline-mode=false\nlevel-type=minecraft\\:flat\ngenerate-structures=false\nmotd=vibecraft-verify\n' "$PORT" > "$RUN/server.properties"
	: > "$STATE/cmds"; rm -f "$LOG"
	cd "$ROOT"
	( { tail -f "$STATE/cmds" & echo $! > "$STATE/tail.pid"; wait; } | ./gradlew runServer --console=plain > "$STATE/server.out" 2>&1 ) &
	echo $! > "$STATE/server.pid"
	if wait_log 'Done \(.*\)! For help' 300; then echo "ready on port $PORT"; else tail -20 "$STATE/server.out" >&2; exit 1; fi
	;;
doctor)
	ok=0
	alive server && echo "ok   launcher process $(cat "$STATE/server.pid") alive" || { echo "FAIL no server started by this harness"; ok=1; }
	grep -Eq 'Done \(.*\)! For help' "$LOG" 2>/dev/null && echo "ok   server finished starting" || { echo "FAIL no 'Done' line in $LOG"; ok=1; }
	grep -q 'VibeCraft loaded' "$LOG" 2>/dev/null && echo "ok   mod initialised" || { echo "FAIL 'VibeCraft loaded' not in log"; ok=1; }
	(exec 3<>"/dev/tcp/127.0.0.1/$PORT") 2>/dev/null && echo "ok   port $PORT accepting connections" || { echo "FAIL port $PORT closed"; ok=1; }
	grep -m1 -o 'vibecraft [0-9][^,]*' "$LOG" 2>/dev/null | sed 's/^/info mod version: /'
	exit $ok
	;;
send)
	shift
	alive server || { echo "server not running" >&2; exit 1; }
	echo "$*" >> "$STATE/cmds"
	;;
wait-log)
	wait_log "$2" "${3:-60}"
	;;
evidence)
	out="$RUN/evidence/${2:?name required}"
	mkdir -p "$out"
	cp "$LOG" "$out/latest.log"
	cp "$STATE/cmds" "$out/console-input.txt"
	git -C "$ROOT" rev-parse HEAD > "$out/commit.txt" 2>/dev/null
	git -C "$ROOT" status --short > "$out/dirty-files.txt" 2>/dev/null
	echo "$out"
	;;
daemon)
	# Runs the daemon entry point from the packaged jar, outside the game, on the
	# JDK 25 that Gradle provisioned (the system java may be older).
	shift
	java25="$(find "${GRADLE_USER_HOME:-$HOME/.gradle}/jdks" -maxdepth 4 -path '*-25-*' \( -name java -o -name java.exe \) 2>/dev/null | head -1)"
	[ -n "$java25" ] || { echo "no Gradle-provisioned JDK 25 found; run ./gradlew build once" >&2; exit 1; }
	jar="$(ls "$ROOT"/build/libs/vibecraft-*.jar 2>/dev/null | grep -v sources | head -1)"
	[ -n "$jar" ] || { echo "no jar in build/libs; run ./gradlew build" >&2; exit 1; }
	"$java25" -cp "$jar" io.github.watsonjph.vibecraft.daemon.DaemonMain "$@"
	;;
stop)
	if alive server; then
		echo "stop" >> "$STATE/cmds"
		i=0; while alive server && [ "$i" -lt 60 ]; do sleep 1; i=$((i + 1)); done
		alive server && kill "$(cat "$STATE/server.pid")" 2>/dev/null
	fi
	alive tail && kill "$(cat "$STATE/tail.pid")" 2>/dev/null
	rm -f "$STATE/server.pid" "$STATE/tail.pid"
	echo "stopped"
	;;
*)
	sed -n '2,3p' "$0"; exit 2
	;;
esac
