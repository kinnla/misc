/*
 * Created on 18.11.2004
 *
 * TODO To change the template for this generated file go to
 * Window - Preferences - Java - Code Style - Code Templates
 */
package einstein.unredo;

import einstein.Collage;

/**
 * @author zoppke
 *
 * TODO
 */
public class PushUpUnredo implements Unredo {

    private Collage collage;

    /**
     * @param layer
     */
    public PushUpUnredo(Collage collage) {
        super();
        this.collage = collage;
    }

    /*
     * (non-Javadoc)
     * 
     * @see einstein.unredo.Unredo#undo()
     */
    public void undo() {
        collage.pushDown();
    }

    /*
     * (non-Javadoc)
     * 
     * @see einstein.unredo.Unredo#redo()
     */
    public void redo() {
        collage.pushUp();
    }

}
