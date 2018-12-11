import {Component, OnInit, ViewChild} from '@angular/core';
import {MatDialog} from '@angular/material';
import {MessageComponent} from '../message/message.component';

@Component({
  selector: 'app-display',
  templateUrl: './display.component.html',
  styleUrls: ['./display.component.css']
})
export class DisplayComponent implements OnInit
{
  @ViewChild('imageContainer') imageContainer;

  allImages = [];
  images = [];
  savedStateImages = [];
  tileWidth = '600px';
  tileHeight = '200px';
  columns = 1;
  rows = 1;
  uniqueCenters = [];
  uniqueTypes = [];
  shareUrl = '<No images loaded>';

  constructor(private dialog: MatDialog)
  {
  }

  ngOnInit()
  {
  }

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

  setShareUrl(url: string): void
  {
    this.shareUrl = url;
  }

  showShareUrl(): void
  {
    this.dialog.open(MessageComponent, {
      width: '850px',
      height: '200px',
      data: {'title': 'Shareable URL', 'message': this.shareUrl}
    });
  }

  downloadImages(): void
  {
    this.dialog.open(MessageComponent, {
      width: '850px',
      height: '200px',
      data: {'title': 'Download Images', 'message': 'Sorry, this feature is not implemented yet'}
    });
  }

  recomputeGrid(): void
  {
    /* find some important values */
    const imgRatio = 1.25;
    const width = this.imageContainer.nativeElement.clientWidth - 225; /* subtract the image selector list */
    const height = this.imageContainer.nativeElement.clientHeight;

    /* count the number of selected images */
    let selectedImages = 0;
    for (let i = 0; i < this.images.length; i++)
    {
      if (this.images[i].selected)
      {
        selectedImages++;
      }
    }

    for (let cols = 1; cols <= selectedImages; cols++)
    {
      let aWidth = (width - (15 * cols - 1)) / cols; /* the perfect width for one image with 'a' columns */
      const aNumRows = Math.ceil(selectedImages / cols);
      let aTotalHeight = (15 * aNumRows - 1) + aNumRows * aWidth / imgRatio;

      if (aTotalHeight < height || cols === selectedImages)
      {
        this.columns = cols;
        this.rows = Math.ceil(selectedImages / cols);
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
  }

  selectOnlyCenter(center: string): void
  {
    for (let i = 0; i < this.allImages.length; i++)
    {
      this.allImages[i].selected = (this.allImages[i].center === center);
    }
    this.setImages(this.allImages);
  }


  selectOnlyType(type: string): void
  {
    for (let i = 0; i < this.allImages.length; i++)
    {
      this.allImages[i].selected = (this.allImages[i].type === type);
    }
    this.setImages(this.allImages);
  }

  selectAll(): void
  {
    for (let i = 0; i < this.allImages.length; i++)
    {
      this.allImages[i].selected = true;
    }
    this.setImages(this.allImages);
  }

  selectNone(): void
  {
    for (let i = 0; i < this.allImages.length; i++)
    {
      this.allImages[i].selected = false;
    }
    this.setImages(this.allImages);
  }

  toggleSingleImage(event): void
  {
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
      const singleImage = [];
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
}
