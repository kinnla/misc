package tree;
/**
 * FU-Berlin, WS 03/04, Alp3, Aufgabe 35.
 * Implementierung von 2-3-B�umen, die alle Schl�ssel in den Bl�ttern speichern.
 * 
 * Qualitative Beurteilung der Software
 * - Korrektheit: Das Programm ist korrekt (jedenfalls nach meinem Testlauf)
 * - Effizienz: Die Funktion "add(int):void" ben�tigt h^2 (H=H�he) Laufzeit.
 *   M�glich w�re h. Die anderen Funktionen sind (asymptotisch) optimal.
 * - Architektur: Ein Schnittstelle ist durch die abstrakte Klasse "Tree"
 *   gegeben.
 * - Implementierung: Die Verwendung der Klasse "Integer" f�r einen Blattknoten
 *   ist ung�nstig. Einigen Code gibt es doppelt, z.B. beim Einf�gen eines
 *   Blattes und eines inneren Knoten. Besser: Abstrakte Klasse Node mit 
 *   konkreten Unterklassen "Leaf" und "InnerNode".
 * - Dokumentation: Die wichtigsten Stellen sind dokumentiert 
 *  
 * @author zoppke
 */
public class TwoThree2 extends Tree {

	private int size = 0;
	private int height = -1;
	private Object root;

	// Laufzeit O(1)
	public int size() {
		return size;
	}

	// Laufzeit O(1)
	public boolean isEmpty() {
		return size == 0;
	}

	// Laufzeit O(1)
	public int height() {
		return height;
	}

	// Laufzeit O(h)
	public boolean contains(int key) {
		// Ein leerer Baum enth�lt keinen Schl�ssel
		if (size == 0) {
			return false;
		}
		// Ein Baum der Gr��e 1 enth�lt genau einen Schl�ssel
		if (size == 1) {
			return ((Integer) root).intValue() == key;
		}
		// suche den Schl�ssel im Baum.
		Node v = lookup(key);
		// v ist nun Vater eines Blattes. 
		// Suche den Schl�ssel bei seinen Kindern.
		return v.contains(key);
	}

	// Laufzeit O(h)
	public int minimum() throws EmptyTreeException {
		// Ein leerer Baum hat kein Minimum.
		if (size == 0) {
			throw new EmptyTreeException();
		}
		// Ein Baum der Gr��e eins hat sein Minimum in der Wurzel
		if (size == 1) {
			return ((Integer) root).intValue();
		}
		// gebe das minimum vom Unterbaum zur�ck, also des ganzen Baumes
		return minimum((Node) root);
	}

	// Laufzeit O(h)
	public int maximum() throws EmptyTreeException {
		// Ein leerer Baum hat kein Maximum.
		if (size == 0) {
			throw new EmptyTreeException();
		}
		// Ein Baum der Gr��e eins hat sein Maximum in der Wurzel
		if (size == 1) {
			return ((Integer) root).intValue();
		}
		// Wandere nach rechts bis zu einem Blatt
		Node v = (Node) root;
		while (!v.nearLeaf()) {
			v = (Node) (!v.full() ? v.mid : v.right);
		}
		// und gebe den Schl�ssel zur�ck
		return !v.full() ? v.midVal() : v.rightVal();
	}

	// Laufzeit O(h^2)
	public void add(int key) {
		// In einen leeren Baum f�gen wir den Schl�ssel als Wurzel ein. 
		if (size == 0) {
			root = new Integer(key);
			size = 1;
			height = 0;
			return;
		}
		// in einen Baum der Gr��e 1 f�gen setzen wir einen neuen inneren
		// Knoten als Wurzel, der die beiden Schl�ssel als Kinder hat.
		if (size == 1) {
			if (key != ((Integer) root).intValue()) {
				root = new Node(null, new Integer(key), (Integer) root);
				size = 2;
				height = 1;
			}
			return;
		}
		// andernfalls suchen wir nach der richtigen Einf�gestelle
		Node v = lookup(key);
		// falls der Wert schon gespeichert, ist nichts zu tun
		if (v.contains(key)) {
			return;
		}
		// Ansonsten vergr��ert sich der Baum um 1. 
		size++;
		// pr�fe, ob der Knoten noch ein weiteres Kind aufnehmen kann
		if (!v.full()) {
			// F�ge den Knoten hinzu. Die Schl�sselkorrektur �bernimmt die
			// aufgerufene Methode.
			v.add(key);
			return;
		}
		// Der Knoten ist also schon voll. Erzeuge einen neuen Knoten 
		// und f�ge ihn als neues Kind beim Elternknoten hinzu.
		Integer newChild = new Integer(key);
		Node newNode;
		if (key < v.midVal()) {
			// erzeuge neuen Knoten
			newNode = new Node(v.parent, (Integer) v.left, newChild);
			// r�cke Kinder des alten Knotens zurecht
			v.left = v.mid;
			v.mid = v.right;
			v.right = null;
		} else {
			// erzeuge neuen Knoten
			newNode = new Node(v.parent, (Integer) v.right, newChild);
			// l�sche rechtes Kind des alten Knotens
			v.right = null;
		}
		// Passe innere Schl�ssel der Knoten an
		newNode.updateKeys();
		v.updateKeys();
		// Falls wir an der Wurzel, erzeuge neuen Wurzelknoten als Vater
		if (v == root) {
			root = new Node(null, v, newNode);
			height++;
			return;
		}
		// andernfalls f�ge den neuen Knoten beim Vater hinzu.
		 ((Node) v.parent).add(newNode);
	}

	public boolean remove(int key) {
		// nicht implementiert.
		return false;
	}

	// Laufzeit O(1)
	public void clear() {
		// Passe die Wurzelreferenz, die H�he und die Gr��e an
		root = null;
		height = -1;
		size = 0;
	}

	// Laufzeit O(n)
	public int[] toIntArray() {
		// Ein leerer Baum enth�lt keine Schl�ssel
		if (size == 0) {
			return new int[0];
		}
		// ein Baum mit einem Schl�ssel enth�lt einen Schl�ssel
		if (size == 1) {
			return new int[] {((Integer) root).intValue()};
		}
		// Andernfalls traversiere den Baum und sammele die Schl�ssel
		int[] keys = new int[size];
		((Node) root).traverseToIntArray(keys, 0);
		return keys;
	}

	// Laufzeit O(1)
	public String toString() {
		// Leerer Baum
		if (size == 0) {
			return "<leer>\n";
		}
		// Baum mit einem Schl�ssel
		if (size == 1) {
			return "Wurzel:" + root + "\n";
		}
		// Andernfalls sammle Ebene f�r Ebene in einem StringBuffer
		StringBuffer sb = new StringBuffer();
		for (int i = 0; i <= height; ++i) {
			((Node) root).traverseToString(sb, i);
			sb.append("\n");
		}
		// und gebe seinen Inhalt als String zur�ck 
		return sb.toString();
	}

	///////////////////////////// private methods //////////////////////////////

	// Sucht den Vaterknoten des Blattes, das diesen Schl�ssel enth�lt.
	// Falls der Schl�ssel nicht enthalten, wird der Knoten ermittelt,
	// an dem der Wert einzuf�gen w�re.
	private Node lookup(int key) {
		// Wandere bis zu einem Blatt
		Node v = (Node) root;
		while (!v.nearLeaf()) {
			if (key < v.a) {
				v = (Node) v.left;
			} else if (!v.full() || key < v.b) {
				v = (Node) v.mid;
			} else {
				v = (Node) v.right;
			}
		}
		return v;
	}

	// sucht das Minimum des Unterbaumes mit der Wurzel v
	private int minimum(Node v) {
		// Wandere nach links bis zu einem Blatt
		while (!v.nearLeaf()) {
			v = (Node) v.left;
		}
		// und gebe den Schl�ssel zur�ck
		return v.leftVal();
	}

	//////////////////////////// innere Klasse Node ////////////////////////////

	class Node {
		Node parent; // Referenz auf den Elternknoten.
		Object left; // Linkes Kind. Entweder Integer (Blatt) oder Node
		Object mid; // Mittleres Kind. Entweder Integer (Blatt) oder Node
		Object right; // Rechtes Kind. Entweder Integer (Blatt) oder Node
		int a; // erster Schl�ssel
		int b; // zweiter Schl�ssel

		// Konstruktor f�r einen Knoten mit zwei Blatt-Kindern.
		Node(Node parent, Integer child1, Integer child2) {
			if (child1.intValue() > child2.intValue()) {
				a = child1.intValue();
				left = child2;
				mid = child1;
			} else {
				a = child2.intValue();
				left = child1;
				mid = child2;
			}
			this.parent = parent;
		}

		// Konstruktor f�r einen Knoten mit zwei inneren Knoten als Kindern
		Node(Node parent, Node child1, Node child2) {
			// setze Kinder
			if (child1.a > child2.a) {
				left = child2;
				mid = child1;
			} else {
				left = child1;
				mid = child2;
			}
			// setze Referenz auf Elternknoten
			this.parent = parent;
			// setze Elternreferenz der Kinder
			child1.parent = this;
			child2.parent = this;
			// setze Schl�ssel
			a = minimum((Node) mid);
		}

		boolean nearLeaf() {
			return left instanceof Integer;
		}

		boolean contains(int key) {
			return leftVal() == key
				|| midVal() == key
				|| (full() && rightVal() == key);
		}

		int leftVal() {
			return ((Integer) left).intValue();
		}

		int midVal() {
			return ((Integer) mid).intValue();
		}

		int rightVal() {
			return ((Integer) right).intValue();
		}

		// f�gt ein weiteres Blatt zu diesem Knoten hinzu
		void add(int key) {
			// f�ge an richtiger stelle ein
			Integer newChild = new Integer(key);
			if (midVal() < key) {
				right = newChild;
			} else {
				right = mid;
				if (leftVal() < key) {
					mid = newChild;
				} else {
					mid = left;
					left = newChild;
				}
			}
			// passe eigene Schl�ssel an
			updateKeys();
		}

		// f�gt einen weiteren inneren Knoten zu diesem Knoten hinzu. 
		// Auch der kleinste Schl�ssel des neuen Unterbaums wird mitgegeben.
		void add(Node newChild) {
			if (!full()) {
				// F�ge den Knoten an der richtigen Stelle ein.
				if (newChild.a < ((Node) left).a) {
					// r�cke Kinder zurecht
					setRight(mid);
					setMid(left);
					setLeft(newChild);
					// setze Schl�ssel
					b = minimum((Node) right);
					a = minimum((Node) mid);
				} else if (newChild.a < ((Node) mid).a) {
					// r�cke Kind zurecht
					setRight(mid);
					setMid(newChild);
					// setze Schl�ssel
					b = minimum((Node) right);
					a = minimum(newChild);
				} else {
					// f�ge Kind hinzu und setze Schl�ssel
					setRight(newChild);
					b = minimum(newChild);
				}
				// und wir sind fertig.
				return;
			}
			// Der Knoten ist also schon voll. Erzeuge einen neuen Knoten 
			// und f�ge ihn als neues Kind beim Elternknoten hinzu.
			Node newNode;
			if (newChild.a < ((Node) mid).a) {
				// erzeuge neuen Knoten
				newNode = new Node(parent, (Node) left, newChild);
				// r�cke Kinder des alten Knotens zurecht
				setLeft(mid);
				setMid(right);
				// passe Schl�ssel an
				a = b;
			} else {
				// erzeuge neuen Knoten
				newNode = new Node(parent, (Node) right, newChild);
			}
			// l�sche rechtes Kind des alten Knotens
			setRight(null);
			// Falls wir an der Wurzel, erzeuge neuen Wurzelknoten als Vater
			if (this == root) {
				root = new Node(null, this, newNode);
				height++;
				return;
			}
			// andernfalls f�ge den neuen Knoten beim Vater hinzu.
			 ((Node) parent).add(newNode);
		}

		// Die Bl�tter haben sich ge�ndert, passe die inneren Schl�ssel an
		void updateKeys() {
			a = midVal();
			if (full()) {
				b = rightVal();
			}
		}

		boolean full() {
			return right != null;
		}

		// Traversiert den Baum und speichert die Schl�ssel in ein Array
		// Rekursive Hilfsfunktion f�r Tree.toIntArray
		int traverseToIntArray(int[] keys, int k) {
			if (nearLeaf()) {
				keys[k++] = leftVal();
				keys[k++] = midVal();
				if (full()) {
					keys[k++] = rightVal();
				}
			} else {
				k = ((Node) left).traverseToIntArray(keys, k);
				k = ((Node) mid).traverseToIntArray(keys, k);
				if (full()) {
					k = ((Node) right).traverseToIntArray(keys, k);
				}
			}
			return k;
		}

		// Erzeugt eine Zeichenkette f�r eine Ebene des Baumes. 
		// Rekursive Hilfsfunktion f�r Tree.toString
		void traverseToString(StringBuffer sb, int level) {
			// Falls wir auf der gefragten Ebene angekommen, 
			// gebe einen String f�r diesen Knoten zur�ck 
			if (level == 0) {
				sb.append(this);
			}
			// pr�fe nun, ob wir bei den Bl�ttern sind
			else if (nearLeaf()) {
				// F�ge die Schl�ssel der Bl�tter hinzu
				sb.append("[");
				sb.append(leftVal());
				sb.append(",");
				sb.append(midVal());
				if (full()) {
					sb.append(",");
					sb.append(rightVal());
				}
				sb.append("]");
			}
			// Andernfalls rufe die Funktion rekursiv f�r alle Kinder auf.
			else {
				sb.append("<");
				((Node) left).traverseToString(sb, level - 1);
				((Node) mid).traverseToString(sb, level - 1);
				if (full()) {
					((Node) right).traverseToString(sb, level - 1);
				}
				sb.append(">");
			}
		}

		public String toString() {
			String s = "<" + a;
			if (full()) {
				s = s + "," + b;
			}
			return s += ">";
		}

		void setLeft(Object child) {
			left = child;
			if (child != null && child instanceof Node) {
				((Node) child).parent = this;
			}
		}

		void setMid(Object child) {
			mid = child;
			if (child != null && child instanceof Node) {
				((Node) child).parent = this;
			}
		}

		void setRight(Object child) {
			right = child;
			if (child != null && child instanceof Node) {
				((Node) child).parent = this;
			}
		}
	}
}
/*
Gr��e des leeren Baumes: 0
Ist der leere Baum leer?: true
H�he des leeren Baumes: -1
Ist Schl�ssel 1 im leeren Baum?: false
Minimum im leeren Baum: exception.
Maximum im leeren Baum: exception.
Entfernen im leeren Baum: false
Zahlenfolge im leeren Baum: []
Stringausgabe vom leeren Baum: <leer>

F�ge Schl�ssel 1 hinzu:
Schl�ssel 1 hinzugef�gt.
Gr��e des 1-Baumes: 1
Ist der 1-Baum leer?: false
H�he des 1-Baumes: 0
Ist Schl�ssel 1 im 1-Baum?: true
Ist Schl�ssel 2 im 1-Baum?: false
Ist Schl�ssel 0 im 1-Baum?: false
Minimum im 1-Baum: 1
Maximum im 1-Baum: 1
Zahlenfolge im 1-Baum: [1]
Stringausgabe des 1-Baum: Wurzel:1

F�ge vorhandenen Schl�ssel 1 erneut hinzu.
Schl�ssel 1 hinzugef�gt.
Stringausgabe des 1-Baum: Wurzel:1

Entferne 2 aus dem 1-Baum: false
Entferne 0 aus dem 1-Baum: false
Entferne 1 aus dem 1-Baum: false
Stringausgabe des leeren Baumes: Wurzel:1

Entferne 1 noch einmal: false
Und noch einmal Stringausgabe: Wurzel:1

Und die Zahlenfolge: [1]
F�ge die Schl�ssel 1 und 2 hinzu:
Schl�ssel 1 und 2 hinzugef�gt.
Gr��e des 1-2-Baumes: 2
Ist der 1-2-Baum leer?: false
H�he des 1-2-Baumes: 1
Ist Schl�ssel 1 im 1-2-Baum?: true
Ist Schl�ssel 2 im 1-2-Baum?: true
Ist Schl�ssel 0 im 1-2-Baum?: false
Ist Schl�ssel 3 im 1-2-Baum?: false
Minimum im 1-2-Baum: 1
Maximum im 1-2-Baum: 2
Stringausgabe vom 1-2-Baum: <2>
[1,2]

Zahlenfolge im 1-2-Baum: [1,2]
F�ge vorhandene Schl�ssel 1 und 2 erneut hinzu.
Schl�ssel 1 und 2 hinzugef�gt.
Stringausgabe des 1-2-Baum: <2>
[1,2]

Entferne 3 aus dem 1-2-Baum: false
Entferne 0 aus dem 1-2-Baum: false
Entferne 1 aus dem 1-2-Baum: false
Stringausgabe des 2-Baumes: <2>
[1,2]

Entferne 1 noch einmal: false
Und noch einmal Stringausgabe: <2>
[1,2]

Entferne 2 aus dem 1-Baum: false
Stringausgabe leeren Baumes: <2>
[1,2]

Und die Zahlenfolge: [1,2]
F�ge die Schl�ssel 1, 2 und 3 hinzu:
Schl�ssel 1, 2 und 3 hinzugef�gt.
Gr��e des 1-2-3-Baumes: 3
Ist der 1-2-3-Baum leer?: false
H�he des 1-2-3-Baumes: 1
Ist Schl�ssel 1 im 1-2-3-Baum?: true
Ist Schl�ssel 2 im 1-2-3-Baum?: true
Ist Schl�ssel 3 im 1-2-3-Baum?: true
Ist Schl�ssel 0 im 1-2-3-Baum?: false
Ist Schl�ssel 4 im 1-2-3-Baum?: false
Minimum im 1-2-3-Baum: 1
Maximum im 1-2-3-Baum: 3
Stringausgabe vom 1-2-3-Baum: <2,3>
[1,2,3]

Zahlenfolge im 1-2-3-Baum: [1,2,3]
F�ge vorhandene Schl�ssel 1, 2 und 2 erneut hinzu.
Schl�ssel 1, 2 und 3 hinzugef�gt.
Stringausgabe des 1-2-3-Baum: <2,3>
[1,2,3]

Entferne 4 aus dem 1-Baum: false
Entferne 0 aus dem 1-Baum: false
Entferne 1 aus dem 1-Baum: false
Stringausgabe des 2-3-Baumes: <2,3>
[1,2,3]

Entferne 1 noch einmal: false
Und noch einmal Stringausgabe: <2,3>
[1,2,3]

Entferne 2 aus dem 2-3-Baum: false
Stringausgabe 3-Baumes: <2,3>
[1,2,3]

leere den 3-Baum.
Stringausgabe des leeren Baumes: <leer>

Und die Zahlenfolge: []
F�ge die Schl�ssel 1, 2, 3 und 4 hinzu:
Schl�ssel 1, 2, 3 und 4 hinzugef�gt.
Gr��e des 1-2-3-4-Baumes: 4
Ist der 1-2-3-4-Baum leer?: false
H�he des 1-2-3-4-Baumes: 2
Ist Schl�ssel 1 im 1-2-3-4-Baum?: true
Ist Schl�ssel 2 im 1-2-3-4-Baum?: true
Ist Schl�ssel 3 im 1-2-3-4-Baum?: true
Ist Schl�ssel 0 im 1-2-3-4-Baum?: false
Ist Schl�ssel 4 im 1-2-3-4-Baum?: true
Ist Schl�ssel 5 im 1-2-3-4-Baum?: false
Minimum im 1-2-3-4-Baum: 1
Maximum im 1-2-3-4-Baum: 4
Stringausgabe vom 1-2-3-4-Baum: <3>
<<2><4>>
<[1,2][3,4]>

Zahlenfolge im 1-2-3-4-Baum: [1,2,3,4]
F�ge vorhandene Schl�ssel 1, 2, 3 und 4 erneut hinzu.
Schl�ssel 1, 2, 3 und 4 hinzugef�gt.
Stringausgabe des 1-2-3-4-Baum: <3>
<<2><4>>
<[1,2][3,4]>

Entferne 4 aus dem 1-Baum: false
Entferne 0 aus dem 1-Baum: false
Entferne 1 aus dem 1-Baum: false
Stringausgabe des 2-3-Baumes: <3>
<<2><4>>
<[1,2][3,4]>

Entferne 1 noch einmal: false
Und noch einmal Stringausgabe: <3>
<<2><4>>
<[1,2][3,4]>

Entferne 2 aus dem 2-3-Baum: false
Stringausgabe 3-Baumes: <3>
<<2><4>>
<[1,2][3,4]>

leere den 3-Baum.
Stringausgabe des leeren Baumes: <leer>

Und die Zahlenfolge: []
+++++++++++ Test durch Zufall ++++++++++++
Zufall ok.
++++++++++++++ Testlauf beendet ++++++++++++++
*/