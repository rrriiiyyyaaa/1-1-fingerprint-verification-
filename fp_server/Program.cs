using System.Drawing;
using System.Drawing.Imaging;
using System.Net.Http.Headers;
using SecuGen.FDxSDKPro.Windows;
using System.Diagnostics;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.UseDefaultFiles();
app.UseStaticFiles();

SGFingerPrintManager fpm =
    new SGFingerPrintManager();


int imageWidth = 0;
int imageHeight = 0;

bool initialized = false;

// ------------------------------------------------
// INITIALIZE SCANNER
// ------------------------------------------------

Console.WriteLine(
    "Starting fingerprint initialization..."
);

try
{
    int err =
        fpm.Init(SGFPMDeviceName.DEV_AUTO);

    if (err == (int)SGFPMError.ERROR_NONE)
    {
        err = fpm.OpenDevice(
            (int)SGFPMPortAddr.USB_AUTO_DETECT
        );

        if (err == (int)SGFPMError.ERROR_NONE)
        {
            SGFPMDeviceInfoParam info =
                new SGFPMDeviceInfoParam();

            fpm.GetDeviceInfo(info);

            imageWidth = info.ImageWidth;
            imageHeight = info.ImageHeight;

            initialized = true;

            Console.WriteLine(
                $"Scanner ready: {imageWidth}x{imageHeight}"
            );
        }
    }
}
catch (Exception ex)
{
    Console.WriteLine(ex.Message);
}

// ------------------------------------------------
// ENROLLMENT ENDPOINT
// ------------------------------------------------

app.MapGet("/capture", () =>
{
    if (!initialized)
    {
        return Results.BadRequest(new
        {
            success = false,
            message = "Scanner not initialized"
        });
    }

    try
    {
        Console.WriteLine("Waiting for fingerprint...");

        byte[] buffer =
            new byte[imageWidth * imageHeight];

        // wait max 3 sec
        int err = fpm.GetImageEx(
            buffer,
            3000,
            0,
            20
        );

        // timeout / no finger
        if (err != (int)SGFPMError.ERROR_NONE)
        {
            return Results.Ok(new
            {
                success = false,
                timeout = true,
                message = "Timeout: finger not detected"
            });
        }

        // --------------------------------
        // QUALITY CHECK
        // --------------------------------

        int quality = 0;

        fpm.GetImageQuality(
            imageWidth,
            imageHeight,
            buffer,
            ref quality
        );

        Console.WriteLine($"Quality: {quality}");

        // reject bad quality
        if (quality < 60)
        {
            return Results.Ok(new
            {
                success = false,
                quality = quality,
                message = "Poor fingerprint quality"
            });
        }

        // --------------------------------
        // CREATE BITMAP
        // --------------------------------

        using Bitmap bmp = new Bitmap(
            imageWidth,
            imageHeight,
            PixelFormat.Format8bppIndexed
        );

        ColorPalette cp = bmp.Palette;

        for (int i = 0; i < 256; i++)
        {
            cp.Entries[i] =
                Color.FromArgb(i, i, i);
        }

        bmp.Palette = cp;

        BitmapData bmpData = bmp.LockBits(
            new Rectangle(
                0,
                0,
                imageWidth,
                imageHeight
            ),
            ImageLockMode.WriteOnly,
            PixelFormat.Format8bppIndexed
        );

        System.Runtime.InteropServices.Marshal.Copy(
            buffer,
            0,
            bmpData.Scan0,
            buffer.Length
        );

        bmp.UnlockBits(bmpData);

        // convert to TIFF memory
        using Bitmap cloneBmp =
            bmp.Clone(
                new Rectangle(
                    0,
                    0,
                    bmp.Width,
                    bmp.Height
                ),
                PixelFormat.Format24bppRgb
            );

        using MemoryStream ms =
            new MemoryStream();

        cloneBmp.Save(ms, ImageFormat.Tiff);

        byte[] imageBytes = ms.ToArray();

        string base64Image =
            Convert.ToBase64String(imageBytes);

        // SUCCESS
        return Results.Ok(new
        {
            success = true,
            quality = quality,
            image = base64Image
        });
    }
    catch (Exception ex)
    {
        return Results.BadRequest(new
        {
            success = false,
            message = ex.Message
        });
    }
});
// ------------------------------------------------
// AUTO OPEN BROWSER
// ------------------------------------------------

Process.Start(new ProcessStartInfo
{
    FileName =
        "http://localhost:5220/enroll.html",

    UseShellExecute = true
});

// ------------------------------------------------
// RUN SERVER
// ------------------------------------------------

app.Run("http://localhost:5220");