package tree;

import java.util.LinkedList;
import java.util.List;
import java.util.Vector;

/**
 * Ein 2-3-Baum, bei dem Schl�ssel auch in den inneren Knoten gespeichert werden
 * k�nnen. Es wird das Interface Tree implementiert.
 * 
 * @author zoppke
 */
public class TwoThree1 extends Tree {

	int size = 0; // aktuelle Anzahl Schl�ssel im Baum. Zu Beginn 0.
	int height = -1; // aktuelle H�he des Baumes. Zu Beginn -1. 
	Node root = null; // Wurzelknoten. Zu Beginn null.

	// Konstruktor. 
	public TwoThree1() {
		// nichts ist zu tun
	}

	// Gibt die Anzahl der Schl�ssel im Baum zur�ck
	public int size() {
		return size;
	}

	// Gibt die H�he des Baumes wieder
	public int height() {
		return height;
	}

	// �berpr�ft, ob der Baum leer ist
	public boolean isEmpty() {
		return size == 0;
	}

	// Gibt eine Referenz auf die Wurzel zur�ck
	public Node root() {
		return root;
	}

	// Pr�ft, ob dieser Schl�ssel im Baum enthalten
	public boolean contains(int key) {
		// Suche den Knoten. 
		Node v = lookup(key);
		// Pr�fe, ob Baum nicht leer und der Knoten den Schl�ssel enth�lt
		return (v != null && v.contains(key));
	}

	// F�gt einen Schl�ssel zum Baum hinzu
	public void add(int key) {
		// suche Blatt, an dem eingef�gt werden muss
		Node v = lookup(key);
		if (v == null) {
			// Falls leerer Baum, dann stecke den Schl�ssel in eine neue Wurzel
			root = new Node(null, key);
			size = 1;
			height = 0;
		}
		// andernfalls suche entsprechendes Blatt und f�ge dort ein
		else if (!v.contains(key)) {
			v.add(key, null);
			size++;
		}
	}

	// entfernt den Schl�ssel aus dem Baum. Falls der Schl�ssel vorhanden ist,
	// ist der R�ckgabewert true, sonst false.
	public boolean remove(int key) {
		Node v = lookup(key);
		if (v == null || !v.contains(key)) {
			return false;
		}
		// Falls kein Blattknoten, Vertausche Schl�ssel mit kleinstem gr��eren
		// Schl�ssel, der auf jeden Fall in einem Blatt gespeichert ist.
		if (!v.isLeaf()) {
			// starte beim richtigen Kind
			Node child = (v.a == key) ? v.midChild : v.rightChild;
			while (!child.isLeaf()) {
				// laufe dann immer links, bis Blatt erreicht
				child = child.leftChild;
			}
			// vertausche die Schl�ssel
			if (v.a == key) {
				v.a = child.a;
			} else {
				v.b = child.a;
			}
			child.a = key;
			// mache beim Kind weiter
			v = child;
		}
		// V ist nun ein Blatt
		if (v.keys == 2) {
			// Falls zwei Schl�ssel vorhanden, entferne richtigen Schl�ssel
			if (v.a == key) {
				v.a = v.b;
			}
			v.keys = 1;
		} else if (v.isRoot()) {
			// Falls nur ein Schl�ssel vorhanden und dies die Wurzel,
			// setze Wurzel auf null.
			root = null;
		} else {
			// andernfalls markiere Knoten als leer und sage es den Eltern weiter.
			v.keys = 0;
			v.parent.emptyChild();
		}
		// passe verringerte Gr��e an
		size--;
		return true;
	}

	// gibt den kleinsten vorhandenen Schl�ssel zur�ck
	public int minimum() throws EmptyTreeException {
		// suche Knoten mit kleinstem Schl�ssel
		Node v = lookupMin();
		if (v == null) {
			// Falls der Baum leer, Fehler.
			throw new EmptyTreeException();
		} else {
			// andernfalls gib den linken Schl�ssel zur�ck
			return v.a;
		}
	}

	// gibt den gr��ten vorhandenen Schl�ssel zur�ck 
	public int maximum() throws EmptyTreeException {
		// Suche den Knoten mit maximalem Schl�ssel
		Node v = lookupMax();
		if (v == null) {
			// Falls der Baum leer, Fehler.
			throw new EmptyTreeException();
		} else {
			// andernfalls gib den rechten Schl�ssel zur�ck, falls vorhanden
			return (v.keys == 1) ? v.a : v.b;
		}
	}

	// Erzeugt eine inorder-Traversion des Baumes
	public int[] toIntArray() {
		// Rufe rekursive Funktion mit der Wurzel auf
		int[] array = new int[size];
		if (size > 0) {
			traverseIntArray(root, array, 0);
		}
		return array;
	}

	// Leert den Baum
	public void clear() {
		// �berschreibe Wurzelreferenz mit einem Nullpointer und passe Gr��e an 
		root = null;
		size = 0;
	}

	// Ersetzt einen Schl�ssel durch einen anderen
	public void replace(int oldKey, int newKey) throws EmptyTreeException {
		// Entferne alten Schl�ssel, dann f�ge neuen Schl�ssel ein
		remove(oldKey);
		add(newKey);
	}

	// Gibt eine String-Repr�sentation des Baumes zur�ck
	public String toString() {
		String s = "";
		if (root == null) {
			s = "<empty>";
		} else {
			for (int i = 0; i <= height; ++i) {
				//for (int i = 0; i <= 2; ++i) {
				s = s + traverseToString(root, i) + "\n";
			}
		}
		return s;
	}

	// Gibt eine Preorder-Traversierung des Baumes zur�ck
	public List preorder() {
		List nodes = new Vector();
		if (root != null) {
			traverseNodes(nodes, root);
		}
		return nodes;
	}

	// Pr�ft den Baum, ob Unstimmigkeiten entdeckt werden
	public boolean checkNodes() {
		List nodes = preorder();
		int nodeSize = 0;
		for (int i = 0; i < nodes.size(); ++i) {
			nodeSize += ((Node) nodes.get(i)).keys;
			if (!((Node) nodes.get(i)).check()) {
				System.out.println("Bad node: " + nodes.get(i));
				return false;
			}
		}
		if (size != nodeSize) {
			System.out.println(
				"Zahl �ber Knoten: " + nodeSize + ", Size ist: " + size);
			return false;
		}
		if (size > 0 && root == null) {
			System.out.println("Root ist null bei Gr��e " + size);
			return false;
		}
		return true;
	}

	//////////////////////////// private methods /////////////////////////////// 

	// Rekursive Funktion zur inorder-Traversion.
	private int traverseIntArray(Node v, int[] array, int index) {
		if (v.isLeaf()) {
			// Falls wir bei einem Blatt angekommen, f�ge Schl�ssel des Blattes
			// hinzu. Kein weiterer Rekursiver Aufruf
			array[index++] = v.a;
			if (v.keys == 2) {
				array[index++] = v.b;
			}
		} else {
			// besuche alle Kinderknoten. F�ge auch die im Knoten enthaltenen 
			// Schl�ssel an der richtigen Stelle ein.
			index = traverseIntArray(v.leftChild, array, index);
			array[index++] = v.a;
			index = traverseIntArray(v.midChild, array, index);
			if (v.keys == 2) {
				array[index++] = v.b;
				index = traverseIntArray(v.rightChild, array, index);
			}
		}
		return index;
	}

	// rekursive Funktion zur Ausgabe des Baumes
	private String traverseToString(Node v, int level) {
		if (level == 0) {
			return v.toString();
		} else {
			String s = "<";
			if (v.leftChild != null) {
				s += traverseToString(v.leftChild, level - 1);
			}
			if (v.midChild != null) {
				s += traverseToString(v.midChild, level - 1);
			}
			if (v.rightChild != null) {
				s += traverseToString(v.rightChild, level - 1);
			}
			return s + ">";
		}
	}

	// inorder traversion des Baumes, bei der alle Knoten gesammelt werden
	private void traverseNodes(List l, Node v) {
		l.add(v);
		if (v.leftChild != null) {
			traverseNodes(l, v.leftChild);
		}
		if (v.midChild != null) {
			traverseNodes(l, v.midChild);
		}
		if (v.rightChild != null) {
			traverseNodes(l, v.rightChild);
		}
	}

	// sucht den Knoten mit kleinstem Schl�ssel
	private Node lookupMin() {
		// Beginne Suche bei der Wurzel
		Node v = root;
		if (v == null) {
			// Falls keine Wurzel vorhanden, R�ckgabe null
			return null;
		}
		// Gehe zum linken Kind, bis an einem Blatt angekommen
		while (!v.isLeaf()) {
			v = v.leftChild;
		}
		return v;
	}

	// sucht nach dem Knoten, der diesen Schl�ssel enth�lt 
	// oder dem Blatt, wo er eingef�gt werden m�sste. 
	private Node lookup(int key) {
		// Starte bei der Wurzel. Wenn keine Wurzel vorhanden, R�ckgabe null.
		Node v = root;
		if (v == null) {
			return null;
		}
		// solange wir nicht an einem Blatt angekommen sind
		while (!v.isLeaf() && !v.contains(key)) {
			// suche im entsprechenden Kind weiter.
			if (key < v.a) {
				v = v.leftChild;
			} else if (v.keys == 2 && key > v.b) {
				v = v.rightChild;
			} else {
				v = v.midChild;
			}
		}
		return v;
	}

	// sucht den Knoten mit h�chstem Schl�ssel
	private Node lookupMax() {
		// Beginne Suche an der Wurzel. 
		Node v = root;
		if (v == null) {
			// Falls keine Wurzel vorhanden, R�ckgabe null
			return null;
		}
		// Wiederhole, bis an einem Blatt angekommen
		while (!v.isLeaf()) {
			// gehe wenn m�glich zum rechten, sonst zum mittleren Kind
			v = (v.keys == 1) ? v.midChild : v.rightChild;
		}
		return v;
	}

	//////////////////////////// inner class node //////////////////////////////

	// Repr�sentiert einen Knoten im 2-3-Baum
	class Node {
		int keys = 1; // Anzahl Schl�ssel, die dieser Knoten speiichert
		int a; // linker Schl�ssel im Knoten
		int b; // rechter Schl�ssel im Knoten
		Node parent; // Refernz auf Elternknoten
		Node leftChild; // linkes Kind
		Node midChild; // mittleres Kind
		Node rightChild; // rechtes Kind

		// Erzeugt ein neues Blatt mit gegebenem Schl�ssel.
		Node(Node parent, int key) {
			this.parent = parent;
			a = key;
		}

		// Erzeugt einen neuen inneren Knoten mit gegebenem Schl�ssel und zwei
		// Kinderknoten. 
		Node(Node parent, int key, Node leftChild, Node midChild) {
			this(parent, key);
			this.leftChild = leftChild;
			this.midChild = midChild;
			//Der Elternverweis in den Kinderknoten wird gesetzt
			if (leftChild != null) {
				leftChild.parent = this;
			}
			if (midChild != null) {
				midChild.parent = this;
			}
		}

		// Pr�ft diesen Knoten, ob es Unstimmigkeiten gibt
		boolean check() {
			if (leftChild != null && leftChild.parent != this) {
				System.out.println(
					"leftchild's parent is: " + leftChild.parent);
				return false;
			}
			if (midChild != null && midChild.parent != this) {
				System.out.println("midChild's parent is: " + midChild.parent);
				return false;
			}
			if (rightChild != null && rightChild.parent != this) {
				System.out.println(
					"rightChild's parent is: " + rightChild.parent);
				return false;
			}
			if (keys == 0) {
				System.out.println("empty node: " + this);
				return false;
			}
			if (!isLeaf() && childCount() - keys != 1) {
				System.out.println(
					"Knoten hat Schl�ssel: "
						+ keys
						+ ", Kinder: "
						+ childCount());
			}
			return true;
		}

		// Pr�ft, ob dieser Knoten ein Blatt ist
		boolean isLeaf() {
			return childCount() == 0;
		}

		// Pr�ft, ob dieser Schl�ssel im Knoten enthalten
		boolean contains(int key) {
			return a == key || keys == 2 && b == key;
		}

		// pr�ft, ob dieser Knoten die Wurzel ist
		boolean isRoot() {
			return this == root;
		}

		// f�gt einen Schl�ssel und ein Kind zu einem Knoten hinzu
		void add(int key, Node newChild) {
			// Pr�fe, ob schon zwei Schl�ssel gespeichert 
			if (keys == 1) {
				// bisher nur ein Schl�ssel gespeichert. 
				// F�ge neuen Schl�ssel und kind hinzu.
				if (key < a) {
					b = a;
					a = key;
					setRightChild(midChild);
					setMidChild(newChild);
					//System.out.println("7!");
				} else {
					b = key;
					setRightChild(newChild);
					//System.out.println("8!");
				}
				keys = 2;
			} else {
				if (isRoot()) {
					// h�nge zwei neue Kinder an die Wurzel an
					if (key < a) {
						setLeftChild(new Node(this, key, leftChild, newChild));
						setMidChild(new Node(this, b, midChild, rightChild));
						//System.out.println("1!");
					} else if (key < b) {
						setLeftChild(new Node(this, a, leftChild, midChild));
						setMidChild(new Node(this, b, newChild, rightChild));
						a = key;
						//System.out.println("2!");
					} else {
						setLeftChild(new Node(this, a, leftChild, midChild));
						setMidChild(new Node(this, key, rightChild, newChild));
						a = b;
						//System.out.println("3!");
					}
					rightChild = null;
					keys = 1;
					height++;
					System.out.println("Neue H�he: " + height);
					return;
				} else {
					// erschaffe Geschwisterknoten und sende ihn mit
					// neuem Schl�ssel an den Elternknoten.
					Node sibling;
					if (key < a) {
						//System.out.println("4!");
						sibling = new Node(parent, b, midChild, rightChild);
						int temp = a;
						a = key;
						key = temp;
						setMidChild(newChild);
					} else if (key < b) {
						//System.out.println("5!");
						sibling = new Node(parent, b, newChild, rightChild);
					} else {
						//System.out.println("6!");
						sibling = new Node(parent, key, rightChild, newChild);
						key = b;
					}
					keys = 1;
					rightChild = null;
					parent.add(key, sibling);
					return;
				}
			}
		}

		// setzt das linke Kind des Knotens und passt dessen Elternreferenz an
		void setLeftChild(Node v) {
			leftChild = v;
			if (leftChild != null) {
				leftChild.parent = this;
			}
		}

		// setzt das mittlere Kind des Knotens und passt dessen Elternreferenz an
		void setMidChild(Node v) {
			midChild = v;
			if (midChild != null) {
				midChild.parent = this;
			}
		}

		// setzt das rechte Kind des Knotens und passt dessen Elternreferenz an
		void setRightChild(Node v) {
			rightChild = v;
			if (rightChild != null) {
				rightChild.parent = this;
			}
		}

		// Initialisiert den Knoten. Alte Daten werden �berschrieben. 
		// Die neuen Daten werden der Liste entnommen und aus ihr entfernt.
		void init(
			Node parent,
			LinkedList children,
			LinkedList keyList,
			int keys) {

			// setze Elternreferenz
			this.parent = parent;
			// setze linkes Kind
			this.keys = keys;
			if (children.isEmpty()) {
				leftChild = null;
			} else {
				setLeftChild((Node) children.removeFirst());
			}
			// setze ersten Schl�ssel
			a = ((Integer) keyList.removeFirst()).intValue();
			// setze mittleres Kind
			if (children.isEmpty()) {
				midChild = null;
			} else {
				setMidChild((Node) children.removeFirst());
			}
			// Pr�fe, ob ein zweiter Schl�ssel gesetzt werden soll
			if (keys == 1) {
				rightChild = null;
			} else {
				// setze zweiten Schl�ssel
				b = ((Integer) keyList.removeFirst()).intValue();
				// setze rechtes Kind
				if (children.isEmpty()) {
					rightChild = null;
				} else {
					setRightChild((Node) children.removeFirst());
				}
			}
		}

		// Reagiert darauf, dass ein Kind seinen letzten Schl�ssel verloren hat.
		// Wenn m�glich, nimm einen Schl�ssel von den Geschwistern.
		// Ansonsten verschmelze zwei Kinder.
		void emptyChild() {
			// hole Referenzen zu Enkelknoten und Liste aller Schl�ssel
			LinkedList grandChildren = getGrandChildren();
			LinkedList keyList = getChildKeys();
			int diff = grandChildren.size() - keyList.size();
			if (diff != 1 && diff > 0) {
				System.out.println(
					"bei Knoten: "
						+ this
						+ " gibt es Schl�ssel: "
						+ keyList.size()
						+ ", Enkel: "
						+ grandChildren.size());
			}
			switch (keyList.size()) {
				case 2 :
					//System.out.println(":2");
					// Ein weiteres Kind mit einem Schl�ssel. 
					if (isRoot()) {
						// Falls nun die Wurzel leer geworden, 
						// verschmelze Kinder zu neuer Wurzel.
						root.init(null, grandChildren, keyList, 2);
						height--;
						System.out.println("neue H�he: " + height);
					} else {
						// Verschmelze Kinder und leere diesen Knoten.
						// melde dies weiter an den Elternknoten.
						leftChild.init(this, grandChildren, keyList, 2);
						midChild = null;
						rightChild = null;
						keys = 0;
						parent.emptyChild();
					}
					break;
				case 3 :
					//System.out.println(":3");
					// Ein weiteres Kind mit zwei Schl�sseln. 
					// Verteile beide auf zwei Kinder.
					leftChild.init(this, grandChildren, keyList, 1);
					a = ((Integer) keyList.removeFirst()).intValue();
					midChild.init(this, grandChildren, keyList, 1);
					rightChild = null;
					keys = 1;
					break;
				case 4 :
					//System.out.println(":4");
					// zwei weitere Kinder mit je einem Schl�ssel.
					// l�sche leeres Kind, gebe linkem Kind zwei Schl�ssel.
					leftChild.init(this, grandChildren, keyList, 2);
					a = ((Integer) keyList.removeFirst()).intValue();
					midChild.init(this, grandChildren, keyList, 1);
					rightChild = null;
					keys = 1;
					break;
				case 5 :
					//System.out.println(":5");
					// zwei weitere Kinder mit einem bzw. zwei Schl�sseln.
					// Verteile drei Schl�ssel auf drei Kinder.
					leftChild.init(this, grandChildren, keyList, 1);
					a = ((Integer) keyList.removeFirst()).intValue();
					midChild.init(this, grandChildren, keyList, 1);
					b = ((Integer) keyList.removeFirst()).intValue();
					rightChild.init(this, grandChildren, keyList, 1);
					keys = 2;
					break;
				case 6 :
					//System.out.println(":6");
					// zwei weitere Kinder mit je zwei Schl�sseln.
					// Gebe linkem Kind zwei Schl�ssel, den anderen je einen.
					leftChild.init(this, grandChildren, keyList, 2);
					a = ((Integer) keyList.removeFirst()).intValue();
					midChild.init(this, grandChildren, keyList, 1);
					b = ((Integer) keyList.removeFirst()).intValue();
					rightChild.init(this, grandChildren, keyList, 1);
					keys = 2;
					break;
				default :
					System.out.println("Error! falsche Schl�sselzahl!");
			} // ende von switch
		}

		// sammelt alle Enkelknoten in einer aufsteigenden Liste
		LinkedList getGrandChildren() {
			LinkedList grandChildren = new LinkedList();
			grandChildren.add(leftChild.leftChild);
			grandChildren.add(leftChild.midChild);
			grandChildren.add(leftChild.rightChild);
			grandChildren.add(midChild.leftChild);
			grandChildren.add(midChild.midChild);
			grandChildren.add(midChild.rightChild);
			if (rightChild != null) {
				grandChildren.add(rightChild.leftChild);
				grandChildren.add(rightChild.midChild);
				grandChildren.add(rightChild.rightChild);
			}
			// entferne Nullpointer, falls vorhanden (leere Knoten!)
			while (grandChildren.remove(null));
			return grandChildren;
		}

		// Sammelt alle Schl�ssel dieses Knotens und seiner Kinder in einer Liste
		LinkedList getChildKeys() {
			LinkedList keyList = new LinkedList();
			if (leftChild.keys > 0) {
				keyList.add(new Integer(leftChild.a));
				if (leftChild.keys == 2) {
					keyList.add(new Integer(leftChild.b));
				}
			}
			keyList.add(new Integer(a));
			if (midChild.keys > 0) {
				keyList.add(new Integer(midChild.a));
				if (midChild.keys == 2) {
					keyList.add(new Integer(midChild.b));
				}
			}
			if (keys == 2) {
				keyList.add(new Integer(b));
				if (rightChild.keys > 0) {
					keyList.add(new Integer(rightChild.a));
					if (rightChild.keys == 2) {
						keyList.add(new Integer(rightChild.b));
					}
				}
			}
			return keyList;
		}

		// berechnet die Anzahl der Kinder des Knotens
		int childCount() {
			int count = 0;
			if (leftChild != null)
				count++;
			if (midChild != null)
				count++;
			if (rightChild != null)
				count++;
			return count;
		}

		// gibt den Baum als Zeichenkette wieder
		public String toString() {
			String s = "[" + a;
			if (keys == 2) {
				s = s + "," + b;
			}
			return s += "]";
		}
	} // Ende der inneren Klasse Node

	/////////////////////////////// zum Testen /////////////////////////////////

	public static void main(String[] args) {
		TwoThree1 tree = new TwoThree1();
		System.out.println("H�he des leeren Baumes: " + tree.height());
		System.out.println("Gr��e des leeren Baumes: " + tree.size());
		System.out.print("Entfernen im leeren Baum: " + tree.remove(2));
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
		try {
			System.out.print("Ersetzen im leeren Baum: ");
			tree.replace(1, 2);
			System.out.println(" No exception. FEHLER!");
		} catch (EmptyTreeException e) {
			System.out.println("exception.");
		}
		System.out.println("Wurzel des leeren Baumes: " + tree.root());
		System.out.println(
			"Ist Schl�ssel 1 im leeren Baum?: " + tree.contains(1));


		System.out.println(intArrayToString(tree.toIntArray()));
		System.out.println(tree);
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

	// Ausgabe eines Objekt-Arrays
	public static String arrayToString(Object[] array) {
		if (array.length == 0) {
			return "[]";
		}
		String s = "[" + array[0];
		for (int i = 1; i < array.length; ++i) {
			s = s + "," + array[i];
		}
		return s += "]";
	}

	// �berpr�ft, ob ein integer-Array streng aufsteigend sortiert
	public static boolean isSorted(int[] array) {
		for (int i = 1; i < array.length; ++i) {
			if (array[i] <= array[i - 1]) {
				return false;
			}
		}
		return true;
	}
} // Ende von Klasse BTree 
