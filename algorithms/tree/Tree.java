package tree;

/**
 * Klasse Tree f�r einen 2-3-Baum, der ganze Zahlen speichert. 
 * 
 * Diese Klasse enth�lt:
 * - sondierende Funktionen, welche Auskunft �ber den aktuellen Status des
 *   Objektes geben (das sieht viel aus, ist aber wenig).
 * - Methoden zum einf�gen und entfernen (sieht wenig aus, ist aber viel).
 * - Ausgabefunktionen. "toIntArray" ist hilfreich zum Testen, da die Zahlen-
 *   folge streng aufsteigend sortiert sein muss, was sich leicht pr�fen l�sst.
 *   "toString" gibt eine String-Repr�sentation des Baumes zur�ck. Wie die 
 *   aussieht, ist nicht so wichtig. Aber zum Debuggen ist die Funktion 
 *   unverzichtbar.
 * - Testfunktionen. Nach Bedarf erweitern. Hilfreich w�re z.B. eine Funktion
 *   "checkNodes", die pr�ft, ob jedes Kind eines Knotens diesen Knoten auch
 *   zum Elter hat.
 * - Die innere Klasse "EmptyTreeException". 
 * 
 * Was ihr machen soll:
 * - Schreibt eine Klasse (z.B. "MyTree"), welche alle abstrakten Methoden
 *   implementiert.
 * - Entwerft eine weitere Klasse (z.B. "Node") f�r die inneren Knoten des 
 *   Baumes. Die Blattknoten kann man als Integer-Objekte speichern. Oder
 *   man speichert sie gleich in den inneren Knoten der vorletzten Ebene als 
 *   int-Werte. 
 * - Setzt den Testlauf f�r nichtleere B�ume fort. 
 * 
 * Was zu beachten ist:
 * - Die 2-3 B�ume der Vorlesung speichern alle Schl�ssel in den Bl�ttern (dort,
 *   aber nicht nur dort). Achtung: Im Internet finden man meistens eine andere 
 *   Variante. Diese wird nicht akzeptiert.
 * - Implementiert das Einf�gen und Entfernen so, wie es in der Vorlesung
 *   vorgestellt wurde.
 * - Verschwendet nicht systematisch Speicherplatz! Verwendet f�r die 
 *   2 oder 3 Kinder eines inneren Knotens keinen Vector, verwendet f�r die
 *   Blattknoten nicht die gleichen Objekte wie f�r die inneren Knoten.
 * - Euer Baum sollte mit (theoretisch) beliebig gro�en Datenmengen klarkommen,
 *   also keine fest eingebaute Obergrenze haben.
 */
public abstract class Tree {

	///////////////////////// sondierende Funktionen ///////////////////////////

	// bestimmt die Gr��e des Baumes. Ein leerer Baum hat Gr��e 0.
	public abstract int size();

	// ist der Baum leer?
	public abstract boolean isEmpty();

	// bestimmt die H�he des Baumes. Ein leerer Baum hat H�he -1.
	public abstract int height();

	// ist der Schl�ssel enthalten?
	public abstract boolean contains(int key);

	// Gibt das Minimum zur�ck. 
	// Falls der Baum leer ist, wird eine Exception ausgel�st.
	public abstract int minimum() throws EmptyTreeException;

	// Gibt das Maximum zur�ck.
	// Falls der Baum leer ist, wird eine Exception ausgel�st.
	public abstract int maximum() throws EmptyTreeException;

	////////////////////////// Aufbauen und abbauen ////////////////////////////

	// f�gt einen Schl�ssel in den Baum ein
	public abstract void add(int key);

	// l�scht den angegebenen Schl�ssel aus dem Baum.
	// Falls der Schl�ssel gefunden (und gel�scht) wird, ist der R�ckgabewert
	// true, ansonsten false.
	public abstract boolean remove(int key);

	// leert den Baum
	public abstract void clear();

	///////////////////////////////// Ausgabe //////////////////////////////////

	// gibt die im Baum enthaltenen Schl�ssel in aufsteigender Reihenfolge
	// zur�ck.
	public abstract int[] toIntArray();

	// gibt eine Zeichenkette zur�ck, die den Baum darstellt
	public abstract String toString();

	///////////////////////////////// Testen ///////////////////////////////////

	public static void main(String[] args) {
		// Gr��e 0
		Tree tree = new TwoThree2();
		System.out.println("Gr��e des leeren Baumes: " + tree.size());
		System.out.println("Ist der leere Baum leer?: " + tree.isEmpty());
		System.out.println("H�he des leeren Baumes: " + tree.height());
		System.out.println(
			"Ist Schl�ssel 1 im leeren Baum?: " + tree.contains(1));
		try {
			System.out.print("Minimum im leeren Baum: ");
			System.out.println(tree.minimum() + " No exception! FEHLER!");
		} catch (EmptyTreeException e) {
			System.out.println("exception.");
		}
		try {
			System.out.print("Maximum im leeren Baum: ");
			System.out.println(tree.maximum() + " No exception! FEHLER!");
		} catch (EmptyTreeException e) {
			System.out.println("exception.");
		}
		System.out.println("Entfernen im leeren Baum: " + tree.remove(2));
		System.out.println(
			"Zahlenfolge im leeren Baum: "
				+ intArrayToString(tree.toIntArray()));
		System.out.println("Stringausgabe vom leeren Baum: " + tree);
		System.out.println("F�ge Schl�ssel 1 hinzu:");
		tree.add(1);
		System.out.println("Schl�ssel 1 hinzugef�gt.");
		// Gr��e 1
		System.out.println("Gr��e des 1-Baumes: " + tree.size());
		System.out.println("Ist der 1-Baum leer?: " + tree.isEmpty());
		System.out.println("H�he des 1-Baumes: " + tree.height());
		System.out.println("Ist Schl�ssel 1 im 1-Baum?: " + tree.contains(1));
		System.out.println("Ist Schl�ssel 2 im 1-Baum?: " + tree.contains(2));
		System.out.println("Ist Schl�ssel 0 im 1-Baum?: " + tree.contains(0));
		try {
			System.out.print("Minimum im 1-Baum: ");
			System.out.println(tree.minimum());
		} catch (EmptyTreeException e) {
			System.out.println("exception. Fehler!");
		}
		try {
			System.out.print("Maximum im 1-Baum: ");
			System.out.println(tree.maximum());
		} catch (EmptyTreeException e) {
			System.out.println("exception. Fehler!");
		}
		System.out.println(
			"Zahlenfolge im 1-Baum: " + intArrayToString(tree.toIntArray()));
		System.out.println("Stringausgabe des 1-Baum: " + tree);
		System.out.println("F�ge vorhandenen Schl�ssel 1 erneut hinzu.");
		tree.add(1);
		System.out.println("Schl�ssel 1 hinzugef�gt.");
		System.out.println("Stringausgabe des 1-Baum: " + tree);
		System.out.println("Entferne 2 aus dem 1-Baum: " + tree.remove(2));
		System.out.println("Entferne 0 aus dem 1-Baum: " + tree.remove(0));
		System.out.println("Entferne 1 aus dem 1-Baum: " + tree.remove(1));
		System.out.println("Stringausgabe des leeren Baumes: " + tree);
		System.out.println("Entferne 1 noch einmal: " + tree.remove(1));
		System.out.println("Und noch einmal Stringausgabe: " + tree);
		System.out.println(
			"Und die Zahlenfolge: " + intArrayToString(tree.toIntArray()));
		System.out.println("F�ge die Schl�ssel 1 und 2 hinzu: ");
		tree.add(1);
		tree.add(2);
		System.out.println("Schl�ssel 1 und 2 hinzugef�gt.");
		// Gr��e 2
		System.out.println("Gr��e des 1-2-Baumes: " + tree.size());
		System.out.println("Ist der 1-2-Baum leer?: " + tree.isEmpty());
		System.out.println("H�he des 1-2-Baumes: " + tree.height());
		System.out.println("Ist Schl�ssel 1 im 1-2-Baum?: " + tree.contains(1));
		System.out.println("Ist Schl�ssel 2 im 1-2-Baum?: " + tree.contains(2));
		System.out.println("Ist Schl�ssel 0 im 1-2-Baum?: " + tree.contains(0));
		System.out.println("Ist Schl�ssel 3 im 1-2-Baum?: " + tree.contains(3));
		try {
			System.out.print("Minimum im 1-2-Baum: ");
			System.out.println(tree.minimum());
		} catch (EmptyTreeException e) {
			System.out.println("exception. Fehler!");
		}
		try {
			System.out.print("Maximum im 1-2-Baum: ");
			System.out.println(tree.maximum());
		} catch (EmptyTreeException e) {
			System.out.println("exception. Fehler!");
		}
		System.out.println("Stringausgabe vom 1-2-Baum: " + tree);
		System.out.println(
			"Zahlenfolge im 1-2-Baum: " + intArrayToString(tree.toIntArray()));
		System.out.println("F�ge vorhandene Schl�ssel 1 und 2 erneut hinzu.");
		tree.add(1);
		tree.add(2);
		System.out.println("Schl�ssel 1 und 2 hinzugef�gt.");
		System.out.println("Stringausgabe des 1-2-Baum: " + tree);
		System.out.println("Entferne 3 aus dem 1-2-Baum: " + tree.remove(3));
		System.out.println("Entferne 0 aus dem 1-2-Baum: " + tree.remove(0));
		System.out.println("Entferne 1 aus dem 1-2-Baum: " + tree.remove(1));
		System.out.println("Stringausgabe des 2-Baumes: " + tree);
		System.out.println("Entferne 1 noch einmal: " + tree.remove(1));
		System.out.println("Und noch einmal Stringausgabe: " + tree);
		System.out.println("Entferne 2 aus dem 1-Baum: " + tree.remove(2));
		System.out.println("Stringausgabe leeren Baumes: " + tree);
		System.out.println(
			"Und die Zahlenfolge: " + intArrayToString(tree.toIntArray()));
		System.out.println("F�ge die Schl�ssel 1, 2 und 3 hinzu: ");
		tree.add(1);
		tree.add(3);
		tree.add(2);
		System.out.println("Schl�ssel 1, 2 und 3 hinzugef�gt.");
		// Gr��e 3
		System.out.println("Gr��e des 1-2-3-Baumes: " + tree.size());
		System.out.println("Ist der 1-2-3-Baum leer?: " + tree.isEmpty());
		System.out.println("H�he des 1-2-3-Baumes: " + tree.height());
		System.out.println(
			"Ist Schl�ssel 1 im 1-2-3-Baum?: " + tree.contains(1));
		System.out.println(
			"Ist Schl�ssel 2 im 1-2-3-Baum?: " + tree.contains(2));
		System.out.println(
			"Ist Schl�ssel 3 im 1-2-3-Baum?: " + tree.contains(3));
		System.out.println(
			"Ist Schl�ssel 0 im 1-2-3-Baum?: " + tree.contains(0));
		System.out.println(
			"Ist Schl�ssel 4 im 1-2-3-Baum?: " + tree.contains(4));
		try {
			System.out.print("Minimum im 1-2-3-Baum: ");
			System.out.println(tree.minimum());
		} catch (EmptyTreeException e) {
			System.out.println("exception. Fehler!");
		}
		try {
			System.out.print("Maximum im 1-2-3-Baum: ");
			System.out.println(tree.maximum());
		} catch (EmptyTreeException e) {
			System.out.println("exception. Fehler!");
		}
		System.out.println("Stringausgabe vom 1-2-3-Baum: " + tree);
		System.out.println(
			"Zahlenfolge im 1-2-3-Baum: "
				+ intArrayToString(tree.toIntArray()));
		System.out.println(
			"F�ge vorhandene Schl�ssel 1, 2 und 2 erneut hinzu.");
		tree.add(1);
		tree.add(2);
		tree.add(3);
		System.out.println("Schl�ssel 1, 2 und 3 hinzugef�gt.");
		System.out.println("Stringausgabe des 1-2-3-Baum: " + tree);
		System.out.println("Entferne 4 aus dem 1-Baum: " + tree.remove(4));
		System.out.println("Entferne 0 aus dem 1-Baum: " + tree.remove(0));
		System.out.println("Entferne 1 aus dem 1-Baum: " + tree.remove(1));
		System.out.println("Stringausgabe des 2-3-Baumes: " + tree);
		System.out.println("Entferne 1 noch einmal: " + tree.remove(1));
		System.out.println("Und noch einmal Stringausgabe: " + tree);
		System.out.println("Entferne 2 aus dem 2-3-Baum: " + tree.remove(2));
		System.out.println("Stringausgabe 3-Baumes: " + tree);
		System.out.println("leere den 3-Baum.");
		tree.clear();
		System.out.println("Stringausgabe des leeren Baumes: " + tree);
		System.out.println(
			"Und die Zahlenfolge: " + intArrayToString(tree.toIntArray()));
		System.out.println("F�ge die Schl�ssel 1, 2, 3 und 4 hinzu: ");
		tree.add(1);
		tree.add(3);
		tree.add(2);
		tree.add(4);
		System.out.println("Schl�ssel 1, 2, 3 und 4 hinzugef�gt.");
		// Gr��e 4
		System.out.println("Gr��e des 1-2-3-4-Baumes: " + tree.size());
		System.out.println("Ist der 1-2-3-4-Baum leer?: " + tree.isEmpty());
		System.out.println("H�he des 1-2-3-4-Baumes: " + tree.height());
		System.out.println(
			"Ist Schl�ssel 1 im 1-2-3-4-Baum?: " + tree.contains(1));
		System.out.println(
			"Ist Schl�ssel 2 im 1-2-3-4-Baum?: " + tree.contains(2));
		System.out.println(
			"Ist Schl�ssel 3 im 1-2-3-4-Baum?: " + tree.contains(3));
		System.out.println(
			"Ist Schl�ssel 0 im 1-2-3-4-Baum?: " + tree.contains(0));
		System.out.println(
			"Ist Schl�ssel 4 im 1-2-3-4-Baum?: " + tree.contains(4));
		System.out.println(
			"Ist Schl�ssel 5 im 1-2-3-4-Baum?: " + tree.contains(5));
		try {
			System.out.print("Minimum im 1-2-3-4-Baum: ");
			System.out.println(tree.minimum());
		} catch (EmptyTreeException e) {
			System.out.println("exception. Fehler!");
		}
		try {
			System.out.print("Maximum im 1-2-3-4-Baum: ");
			System.out.println(tree.maximum());
		} catch (EmptyTreeException e) {
			System.out.println("exception. Fehler!");
		}
		System.out.println("Stringausgabe vom 1-2-3-4-Baum: " + tree);
		System.out.println(
			"Zahlenfolge im 1-2-3-4-Baum: "
				+ intArrayToString(tree.toIntArray()));
		System.out.println(
			"F�ge vorhandene Schl�ssel 1, 2, 3 und 4 erneut hinzu.");
		tree.add(1);
		tree.add(2);
		tree.add(4);
		tree.add(3);
		System.out.println("Schl�ssel 1, 2, 3 und 4 hinzugef�gt.");
		System.out.println("Stringausgabe des 1-2-3-4-Baum: " + tree);
		System.out.println("Entferne 4 aus dem 1-Baum: " + tree.remove(4));
		System.out.println("Entferne 0 aus dem 1-Baum: " + tree.remove(0));
		System.out.println("Entferne 1 aus dem 1-Baum: " + tree.remove(1));
		System.out.println("Stringausgabe des 2-3-Baumes: " + tree);
		System.out.println("Entferne 1 noch einmal: " + tree.remove(1));
		System.out.println("Und noch einmal Stringausgabe: " + tree);
		System.out.println("Entferne 2 aus dem 2-3-Baum: " + tree.remove(2));
		System.out.println("Stringausgabe 3-Baumes: " + tree);
		System.out.println("leere den 3-Baum.");
		tree.clear();
		System.out.println("Stringausgabe des leeren Baumes: " + tree);
		System.out.println(
			"Und die Zahlenfolge: " + intArrayToString(tree.toIntArray()));
		// Test durch Zufall.
		// Das haut den st�rksten Baum um.
		System.out.println("+++++++++++ Test durch Zufall ++++++++++++");
		boolean error = false;
		for (int i = 0; i < 100 && !error; ++i) {
			tree = new TwoThree2();
			for (int j = 0; j < 1000 && !error; ++j) {
				int number =(int) (Math.random() * 100);
				//System.out.println(tree);
				//System.out.println("adding "+ number);
				tree.add(number);
				int[] keys = tree.toIntArray();
				if (!isSorted(keys)) {
					System.out.println("Unsortierte Zahlenfolge nach Einf�gen!");
					System.out.println(intArrayToString(keys));
					System.out.println(tree);
					error = true;
				} else {
					tree.remove((int) (Math.random() * 100));
					keys = tree.toIntArray();
					if (!isSorted(keys)) {
						System.out.println("Unsortierte Zahlenfolge nach Entfernen!");
						System.out.println(intArrayToString(keys));
						System.out.println(tree);
						error = true;
					}
				}
			}
			//System.out.println(tree);
		}
		if (!error){
			System.out.println("Zufall ok.");
		}
		System.out.println("++++++++++++++ Testlauf beendet ++++++++++++++");
	}

	// Ausgabe eines integer-Arrays
	public static String intArrayToString(int[] array) {
		if (array.length == 0) {
			return "[]";
		}
		String s = "[" + array[0];
		for (int i = 1; i < array.length; ++i) {
			s = s + "," + array[i];
		}
		return s += "]";
	}

	// �berpr�ft, ob ein integer-Array streng aufsteigend sortiert ist
	// F�r so was w�nscht man sich dann wieder haskell...
	public static boolean isSorted(int[] array) {
		for (int i = 1; i < array.length; ++i) {
			if (array[i] <= array[i - 1]) {
				return false;
			}
		}
		return true;
	}

	////////////////////// innere Klasse EmptyTreeException ////////////////////

	class EmptyTreeException extends Exception {
		public EmptyTreeException() {
		}
	}
}
