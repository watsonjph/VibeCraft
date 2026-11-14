package io.github.watsonjph.vibecraft.daemon;

/**
 * Entry point of the agent daemon. Runs as its own JVM, outside the game, so
 * agents survive the game closing. Nothing in this package may import
 * net.minecraft or net.fabricmc: neither is on the daemon's classpath.
 */
public class DaemonMain {
	public static void main(String[] args) {
		System.out.println("vibecraft daemon: not implemented yet (see docs/plan/phase-1-pipe.md)");
	}
}
