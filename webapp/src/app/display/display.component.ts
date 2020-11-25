import {Component, OnInit, ViewChild} from '@angular/core';
import {MatDialog} from '@angular/material';
import {MessageComponent} from '../message/message.component';
import {HttpClient} from '@angular/common/http';
declare var Bokeh: any;

@Component({
  selector: 'app-display',
  templateUrl: './display.component.html',
  styleUrls: ['./display.component.css']
})
export class DisplayComponent implements OnInit
{
  public static singleton: DisplayComponent;


  @ViewChild('imageContainer', {static: false}) imageContainer;
  /* list of all images */
  allImages = [];

  /* list of images to display */
  images = [];

  /* save the state of the images before toggle to single image */
  savedStateImages = [];

  /* the tile width, dynamically updated later */
  tileWidth = '600px';

  /* the tile height, dynamically updated later */
  tileHeight = '200px';

  /* the number of columns for the images */
  columns = 1;

  /* the number of rows for the images */
  rows = 1;

  /* list of unique centers of available images */
  uniqueCenters = [];

  /* list of unique types of available images */
  uniqueTypes = [];

  /* the url to share for this set of images */
  shareUrl = '<No images loaded>';

  /* flag to indicate the interactive plot is being shown */
  showInteractivePlot = false;


  /**
   * Default constructor
   *
   * @param dialog dependency injection
   * @param http dependency injection
   */
  constructor(private dialog: MatDialog, private http: HttpClient)
  {
    DisplayComponent.singleton = this;
  }


  /**
   * Initialize the display component
   */
  ngOnInit()
  {
  }


  /**
   * Set a new list of images to display
   *
   * @param images List of images
   */
  setImages(images): void
  {
    this.allImages = images;
    this.uniqueCenters = [];
    this.uniqueTypes = [];
    this.images = [];
    for (let i = 0; i < this.allImages.length; i++)
    {
      if (this.allImages[i]['selected'] === undefined)
      {
        this.allImages[i].selected = true;
      }
      if (! this.uniqueCenters.includes(this.allImages[i].center))
      {
        this.uniqueCenters[this.uniqueCenters.length] = this.allImages[i].center;
      }
      if (! this.uniqueTypes.includes(this.allImages[i].type))
      {
        this.uniqueTypes[this.uniqueTypes.length] = this.allImages[i].type;
      }
      if (this.allImages[i].selected)
      {
        this.images[this.images.length] = this.allImages[i];
      }
    }
    this.recomputeGrid();
  }


  /**
   * Set the bokeh json data for an image
   * @param key The image key
   * @param data The Bokeh image data
   * @return none
   */
  setJsonData(key: string, data: any): void
  {
    for (const image of this.allImages)
    {
      if (image.key === key)
      {
        image.data = data;
        break;
      }
    }
    this.recomputeGrid();
  }


  /**
   * Calculate the optimal size and layout for the images selected
   */
  recomputeGrid(): void
  {
    /* find some important values */
    const imgRatio = 1.25;
    const width = this.imageContainer.nativeElement.clientWidth - 225; /* subtract the image selector list */
    const height = this.imageContainer.nativeElement.clientHeight;

    /* count the number of selected images */
    let selectedImages = 0;
    for (const image of this.allImages)
    {
      if (image.selected)
      {
        selectedImages++;
      }
    }

    /* set the flag to show a single interactive image */
    this.showInteractivePlot = (selectedImages === 1);

    /* search for optimal number of columns */
    for (let cols = 1; cols <= selectedImages; cols++)
    {
      let aWidth = (width - (15 * cols - 1)) / cols; /* the perfect width for one image with 'a' columns */
      const aNumRows = Math.ceil(selectedImages / cols); /* number of rows based on image width */
      let aTotalHeight = (15 * aNumRows - 1) + aNumRows * aWidth / imgRatio; /* total height based on number of rows and image width */

      /* if we found a good horizontal fit */
      if (aTotalHeight < height || cols === selectedImages)
      {
        /* calculate rows and columns */
        this.columns = cols;
        this.rows = Math.ceil(selectedImages / cols);

        /* shrink the image size until we have a vertical fit */
        while (aTotalHeight > height)
        {
          aWidth -= 10;
          aTotalHeight = (15 * aNumRows - 1) + aNumRows * aWidth / imgRatio;
        }
        this.tileWidth = aWidth + 'px';
        this.tileHeight = (aWidth / imgRatio) + 'px';
        break;
      }
    }

    /* set the json data */
    for (const image of this.images)
    {
      if (image.data !== undefined)
      {
        // Bokeh.embed.embed_item(image.data, image.center + ',' + image.type);
      }
    }
  }


  /**
   * Select only images that match the given center
   *
   * @param center Select all images for this center
   */
  selectOnlyCenter(center: string): void
  {
    for (let i = 0; i < this.allImages.length; i++)
    {
      this.allImages[i].selected = (this.allImages[i].center === center);
    }
    this.setImages(this.allImages);
  }


  /**
   * Select only images that show inter-center comparisons
   */
  selectOnlyComparisons(): void
  {
    for (let i = 0; i < this.allImages.length; i++)
    {
      this.allImages[i].selected = (this.allImages[i].center.startsWith('compare'));
    }
    this.setImages(this.allImages);
  }


  /**
   * Select only images that match the given type
   *
   * @param type Select all images for this type
   */
  selectOnlyType(type: string): void
  {
    for (let i = 0; i < this.allImages.length; i++)
    {
      this.allImages[i].selected = (this.allImages[i].type === type);
    }
    this.setImages(this.allImages);
  }


  /**
   * Select all images
   */
  selectAll(): void
  {
    for (let i = 0; i < this.allImages.length; i++)
    {
      this.allImages[i].selected = true;
    }
    this.setImages(this.allImages);
  }


  /**
   * Show only a single image, or revert to previous view
   *
   * @param event Click event
   */
  toggleSingleImage(event): void
  {
    alert(event.target.id);
    if (this.images.length === 1)
    {
      for (let i = 0; i < this.allImages.length; i++)
      {
        if (this.savedStateImages.includes(this.allImages[i].center + ',' + this.allImages[i].type))
        {
          this.allImages[i].selected = true;
        }
      }
    }
    else
    {
      this.savedStateImages = [];
      const centerAndType = event.target.id.split(',');
      for (let i = 0; i < this.allImages.length; i++)
      {
        if (this.allImages[i].selected)
        {
          this.savedStateImages[this.savedStateImages.length] = this.allImages[i].center + ',' + this.allImages[i].type;
        }
        if (this.allImages[i]['center'] === centerAndType[0] && this.allImages[i]['type'] === centerAndType[1])
        {
          this.allImages[i].selected = true;
        }
        else
        {
          this.allImages[i].selected = false;
        }
      }
    }

    this.setImages(this.allImages);
  }


  /**
   * Show a single, interactive plot
   * @param event Click event
   */
  showSingleInteractivePlot(event): void
  {
    const key = event.target.id.split(',')[0];
    this.showInteractivePlot = true;
    this.images = [];
    for (const image of this.allImages)
    {
      image.selected = (image.key === key);
    }

    this.recomputeGrid();
    for (const image of this.allImages)
    {
      if (image.selected)
      {
        Bokeh.embed.embed_item(image.data, 'interactivePlot');
      }
    }
  }
}
